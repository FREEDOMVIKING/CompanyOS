import smtplib
from email.message import EmailMessage

class SMTPProviderAdapter:
    name="smtp"
    capabilities=["communication"]
    live_supported=True

    def execute(self, request, timeout=30, live=False):
        if not live:
            return {"success":True,"simulated":True,"adapter":self.name,"recipient":request.get("to")}
        msg=EmailMessage()
        msg["From"]=request["from"]
        msg["To"]=request["to"]
        msg["Subject"]=request.get("subject","")
        msg.set_content(request.get("body",""))
        try:
            with smtplib.SMTP(request["host"],int(request.get("port",587)),timeout=timeout) as s:
                if request.get("starttls",True): s.starttls()
                if request.get("username"):
                    s.login(request["username"],request["password"])
                s.send_message(msg)
            return {"success":True,"adapter":self.name,"recipient":request.get("to")}
        except Exception as e:
            return {"success":False,"error_kind":"smtp_error","error":str(e),"adapter":self.name}
