import logging
from threading import Event, Thread
from domain.mail import send_email
from domain.settings import settings, BASE_DIR


def main():
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.DEBUG,
                        datefmt="%H:%M:%S")

    settings.EMAIL_HOST = 'smtp.zoho.com'
    settings.EMAIL_PORT = 465
    settings.EMAIL_USERNAME = 'support@tripvalue.com.ng'
    settings.EMAIL_PASSWORD = 'JxnracXdqYZF'

    event = Event()
    t = Thread(target=send_email, args=(event,), kwargs={
        'csv_file': BASE_DIR / 'test.csv',
        'subject': 'Hello {name}',
        'message': 'Hello {name}',
    })
    t.start()


if __name__ == "__main__":
    main()
