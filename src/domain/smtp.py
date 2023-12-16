import smtplib
import ssl
from contextlib import ContextDecorator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.base import MIMEBase
import logging


class EmailConnection(ContextDecorator):
    """
    This class is responsible for connecting to the
    email server and sending the email.
    """

    def __init__(
        self, host: str, port: int, username: str,
        password: str, sender: str = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection = None
        self.sender = sender
        if sender is None:
            self.sender = username
        self.context = ssl.create_default_context()

    def __enter__(self):
        logging.info('Connecting to the email server')
        if self.port == 465:
            self.connection = smtplib.SMTP_SSL(
                self.host, self.port, context=self.context)
        else:
            self.connection = smtplib.SMTP(self.host, self.port)
            self.connection.starttls(context=self.context)
        logging.info('Logging into the email server')
        self.connection.login(self.username, self.password)
        logging.info('Successfully logged in')
        return self

    def __exit__(self, *exc):
        logging.info('Disconnecting from the email server')
        self.connection.quit()

    def send(
        self, subject: str, recipient: str, text: str,
        html: str = None, attachments: list[str] = None
    ):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = recipient

        message.attach(MIMEText(text, "plain"))
        if html is not None:
            message.attach(MIMEText(html, "html"))

        if attachments is not None:
            for attachment in attachments:
                with open(attachment, "rb") as file:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file.read())
                encoders.encode_base64(part)
                filename = attachment.split("/")[-1]
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                message.attach(part)

        self.connection.sendmail(self.username, recipient, message.as_string())
