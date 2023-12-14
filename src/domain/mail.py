import csv
from threading import Event
import time

from domain.smtp import EmailConnection
from domain.template import renderer
from domain.settings import settings
import logging


def stop(event: Event):
    event.set()


def read_csv(csv_file: str):
    with open(csv_file) as f:
        return f.read()


def send_email(
    event: Event, csv_string: str = '', csv_file: str = '',
    subject: str = '', message: str = '', attachments: list[str] = None
):
    if csv_file:
        csv_string = read_csv(csv_file)
    reader = csv.DictReader(csv_string.splitlines())
    with EmailConnection(
        settings.EMAIL_HOST, settings.EMAIL_PORT,
        settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD
    ) as connection:
        for row in reader:
            if event.is_set():
                logging.debug("Stopped mailing")
                return
            logging.debug(f"Sending email to {row['email']}")
            new_message = message.format(**row)
            text = renderer.render('email.txt', message=new_message)
            html = renderer.render('email.html', message=new_message)
            subject = subject.format(**row)
            connection.send(
                subject=subject,
                recipient=row['email'],
                text=text,
                html=html,
                attachments=attachments
            )

            wait = settings.WAIT_TIME or 5
            logging.info(f"Waiting {wait} seconds")
            event.wait(wait)
        logging.info("Finished sending emails")
        event.set()
