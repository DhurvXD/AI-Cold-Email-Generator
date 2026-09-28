import json
import os
import re
import socket
import ipaddress
import secrets
import time
from urllib.parse import urlparse, urljoin
from http.server import BaseHTTPRequestHandler

import requests
from bs4 import BeautifulSoup

# Allowed models list matching Gen_ai/main.py
ALLOWED_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
]

# Simple in-memory rate limiting: IP -> list of timestamps
RATE_LIMIT_RECORD = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 10  # max requests per minute per IP

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def is_rate_limited(ip: str) -> bool:
    """Check if the requesting IP has exceeded the rate limit."""
    now = time.time()
    timestamps = RATE_LIMIT_RECORD.get(ip, [])
    # Filter out timestamps older than the window
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(valid_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        RATE_LIMIT_RECORD[ip] = valid_timestamps
        return True
    valid_timestamps.append(now)
    RATE_LIMIT_RECORD[ip] = valid_timestamps
    return False


def is_safe_url(url: str) -> tuple[bool, str]:
    """
    Validate that the URL uses HTTP/HTTPS and does NOT resolve
    to localhost, private, reserved, or internal IP spaces (SSRF protection).
    """
    if len(url) > 2048:
        return False, "URL length exceeds maximum permitted limit (2048 characters)."

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ("http", "https"):
        return False, "Only HTTP and HTTPS URLs are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."

    hostname_lower = hostname.lower().strip()
    if hostname_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return False, "Access to localhost or loopback addresses is prohibited."

    # Prevent metadata endpoint access by name
    if "metadata" in hostname_lower or "internal" in hostname_lower:
        return False, "Access to internal hostnames is prohibited."

    # Resolve hostname to all potential IP addresses
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        return False, f"Could not resolve domain '{hostname}': {e}"
    except Exception as e:
        return False, f"DNS resolution failed for '{hostname}': {e}"

    for entry in addr_info:
        ip_str = entry[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            # Check for mapped IPv6 (e.g. ::ffff:192.168.1.1)
            if hasattr(ip, "ipv4_mapped") and ip.ipv4_mapped:
                ip = ip.ipv4_mapped

            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
                or ip.is_unspecified
            ):
                return False, f"Security restriction: IP address '{ip_str}' is private or reserved."

            # Additional cloud metadata check (169.254.169.254)
            if str(ip) == "169.254.169.254":
                return False, "Security restriction: Cloud metadata IP is blocked."

        except ValueError:
            return False, f"Invalid IP address format: '{ip_str}'."

    return True, ""


def fetch_and_clean_job_page(target_url: str) -> tuple[str, str]:
    """
    Fetch the job webpage with SSRF-safe redirect validation and clean the HTML text.
    Returns (cleaned_text, error_message).
    """
    headers = {
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    current_url = target_url
    max_redirects = 3

    for _ in range(max_redirects + 1):
        safe, err = is_safe_url(current_url)
        if not safe:
            return "", f"Target URL or redirect target is unsafe: {err}"

        try:
            resp = requests.get(
                current_url,
                headers=headers,
                timeout=12,
                allow_redirects=False,
            )
        except requests.Timeout:
            return "", "The job posting site timed out while responding (12s limit)."
        except requests.RequestException as e:
            return "", f"Network error while fetching job page: {e}"

        # Handle redirects with safety validation on each hop
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location")
            if not location:
                return "", "Redirect occurred without a valid Location header."
            current_url = urljoin(current_url, location)
            continue
        elif resp.status_code != 200:
            return "", f"Failed to retrieve page: HTTP {resp.status_code} ({resp.reason})."
        else:
            break
    else:
        return "", "Too many redirects occurred while loading the job page."

    # Parse and extract readable content with BeautifulSoup
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove noisy elements
        for element in soup(["script", "style", "nav", "header", "footer", "noscript", "svg", "form", "iframe"]):
            element.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Collapse multiple whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 60:
            return "", (
                "The page returned very little or no readable text. "
                "The target site may require JavaScript, login, or be blocking automated access."
            )

        # Truncate to approx 12,000 characters to stay within model context limits
        truncated_text = text[:12000]
        return truncated_text, ""

    except Exception as e:
        return "", f"Failed to parse page content: {e}"


def call_groq_api(page_data: str, sender_name: str, sender_role: str, model_name: str) -> tuple[str, str]:
    """
    Call Groq chat completions API directly with plain HTTP request.
    Returns (email_text, error_message).
    """
    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not groq_api_key:
        return "", "GROQ_API_KEY environment variable is not configured on the server."

    prompt = f"""
### JOB DESCRIPTION:
{page_data}

### INSTRUCTION:
You are {sender_name}, a {sender_role}.
Your job is to write a compelling, tailored cold outreach email to the hiring manager or client regarding the job opportunity mentioned above.
Highlight how your team's skills, expertise, and solutions can help fulfill their business needs and solve their challenges.
Do not provide any preamble, intro remarks, or conversational filler. Output only the email starting with the subject line.

### EMAIL (NO PREAMBLE):
"""

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=35,
        )

        if response.status_code != 200:
            try:
                err_data = response.json()
                api_err = err_data.get("error", {}).get("message", response.text)
            except Exception:
                api_err = response.text
            return "", f"Groq API error ({response.status_code}): {api_err}"

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return "", "Groq API returned an empty response."

        email_content = choices[0].get("message", {}).get("content", "").strip()
        return email_content, ""

    except requests.Timeout:
        return "", "Groq API request timed out (35s limit). Please retry."
    except requests.RequestException as e:
        return "", f"Failed to communicate with Groq API: {e}"


class handler(BaseHTTPRequestHandler):
    """Vercel Python Serverless HTTP Request Handler."""

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        """Handle cold email generation requests."""
        client_ip = (
            self.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or self.headers.get("x-real-ip", "")
            or self.client_address[0]
        )

        # Rate limiting check
        if is_rate_limited(client_ip):
            self._send_json(429, {"error": "Rate limit exceeded. Please wait a minute before trying again."})
            return

        # Check payload length
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length <= 0 or content_length > 100000:
            self._send_json(400, {"error": "Invalid request body or size exceeds 100KB limit."})
            return

        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body)
        except Exception:
            self._send_json(400, {"error": "Malformed JSON payload."})
            return

        # 1. Passcode Validation
        expected_passcode = os.environ.get("APP_PASSCODE", "").strip()
        user_passcode = str(payload.get("passcode", "")).strip()

        if expected_passcode:
            if not user_passcode or not secrets.compare_digest(user_passcode, expected_passcode):
                self._send_json(401, {"error": "Invalid or missing application passcode."})
                return
        else:
            # If APP_PASSCODE is not set on the server, reject with helpful message to prevent open proxy abuse
            self._send_json(
                500,
                {
                    "error": (
                        "Server configuration error: APP_PASSCODE is not configured in Vercel environment variables."
                    )
                },
            )
            return

        # 2. Input Limits & Sanitization
        job_url = str(payload.get("url", "")).strip()
        sender_name = str(payload.get("sender_name", "Mohan")).strip()[:100]
        sender_role = str(payload.get("sender_role", "Business Development Executive at AtliQ")).strip()[:200]
        model = str(payload.get("model", "openai/gpt-oss-20b")).strip()

        if not job_url:
            self._send_json(400, {"error": "Job posting URL is required."})
            return

        if not sender_name:
            sender_name = "Mohan"
        if not sender_role:
            sender_role = "Business Development Executive at AtliQ"

        if model not in ALLOWED_MODELS:
            model = "openai/gpt-oss-20b"

        # 3. Fetch Job Description (with SSRF security checks)
        cleaned_text, fetch_err = fetch_and_clean_job_page(job_url)
        if fetch_err:
            self._send_json(400, {"error": fetch_err})
            return

        # 4. Generate Cold Email via Groq API
        email_content, groq_err = call_groq_api(cleaned_text, sender_name, sender_role, model)
        if groq_err:
            self._send_json(502, {"error": groq_err})
            return

        # 5. Return Success Response
        self._send_json(
            200,
            {
                "success": True,
                "email": email_content,
                "model": model,
                "job_chars_parsed": len(cleaned_text),
            },
        )
