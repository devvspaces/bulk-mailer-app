import csv
from threading import Event

from domain.smtp import EmailConnection
from domain.template import renderer
from domain.settings import settings
import logging


WAIT_TIME = 5


def stop(event: Event):
    event.set()


def read_csv(csv_file: str):
    with open(csv_file) as f:
        return f.read()


class EmailCounter:
    """Counts the number of emails sent."""

    def __init__(self):
        self._count = 0
        self._total = 0

    def get_total(self):
        return self._total

    def set_total(self, total: int):
        self._total = total

    def __iadd__(self, other):
        self._count += other
        return self

    def __str__(self):
        return str(self._count)


def send_email(
    event: Event,
    csv_string: str = "",
    csv_file: str = "",
    subject: str = "",
    message: str = "",
    sender: str = "",
    attachments: list[str] = None,
    counter: EmailCounter = None,
):
    if csv_file:
        csv_string = read_csv(csv_file)
    reader = csv.DictReader(csv_string.splitlines())

    l_reader = list(reader)

    # Set total emails to send
    if counter:
        counter.set_total(len(l_reader))

    with EmailConnection(
        settings.EMAIL_HOST,
        settings.EMAIL_PORT,
        settings.EMAIL_USERNAME,
        settings.EMAIL_PASSWORD,
        sender
    ) as connection:
        for index, row in enumerate(l_reader):
            if event.is_set():
                logging.debug("Stopped mailing")
                return
            logging.debug(f"Sending email to {row['email']}")
            new_message = message.format(**row)
            text = renderer.render("email.txt", message=new_message)
            html = renderer.render("email.html", message=new_message)
            subject = subject.format(**row)
            try:
                connection.send(
                    subject=subject,
                    recipient=row["email"],
                    text=text,
                    html=html,
                    attachments=attachments,
                )
                if counter:
                    counter += 1
            except Exception as e:
                logging.error(f"Error sending email to {row['email']}")
                logging.exception(e)
                continue

            if index == len(l_reader) - 1:
                break

            wait = settings.WAIT_TIME
            if not settings.WAIT_TIME:
                logging.info(f"Using default wait time of {WAIT_TIME} seconds")
                wait = WAIT_TIME

            logging.info(f"Waiting {wait} seconds")
            event.wait(wait)
        logging.info("Finished sending emails")
        event.set()
