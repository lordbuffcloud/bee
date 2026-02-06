import smtplib
from email.message import EmailMessage


class EmailClient:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str) -> None:
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send(self, to_email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self.username
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(message)
