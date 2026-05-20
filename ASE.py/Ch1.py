class Application:
    def __init__(self, name, status):
     self.name = name 
     self.status = status

    def check_status(self):
        print(f"Application = {self.name} | Status = {self.status}")


class CriticalApplication(Application):
    def __init__(self, name, status, priority):
     super().__init__(name, status)
     self.priority = priority

    def alert(self):
        print(f"ALERT = {self.name} is {self.status}! Priority : {self.priority}")

app1 = Application("Payment portal", "Running")
app1.check_status()

app2 = CriticalApplication("Loan System", "Down", "P1")
app2.check_status()
app2.alert()
