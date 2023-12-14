from cmd import Cmd
import sys
from domain.mail import send_email
from domain.settings import BASE_DIR, settings
from threading import Event, Thread
import logging

format = "%(asctime)s: %(message)s"
file_handler = logging.FileHandler(BASE_DIR / 'mailer.log')
logging.basicConfig(
    format=format, level=logging.DEBUG,
    datefmt="%H:%M:%S", handlers=[file_handler])

event = Event()

class MailerShell(Cmd):
    intro = 'Welcome to the Bulk Mailer shell. \
Type help or ? to list commands.\n'
    prompt = '(mailer) '

    subject = ''
    message = ''

    def do_send(self, arg: str):
        'Send an email to a list of recipients in a file'
        if not arg:
            print('Please provide a file')
            return
        if not self.subject:
            print('Please provide a subject: subject Hello {name}')
            return
        if not self.message:
            print('Please provide a message: message Hello {name}')
            return

        event.clear()
        t = Thread(target=send_email, args=(event,), kwargs={
            'csv_file': BASE_DIR / arg,
            'subject': self.subject,
            'message': self.message,
        })
        t.start()

    def do_subject(self, arg: str):
        'Set the subject for the email: subject Hello {name}'
        self.subject = arg

    def do_message(self, arg: str):
        'Set the message for the email: message Hello {name}'
        self.message = arg

    def do_settings(self, arg: str):
        'Change settings for the mailer: settings EMAIL_HOST smtp.zoho.com'
        key, value = arg.split()
        setattr(settings, key, value)

    def do_show(self, arg):
        'Show the current settings'
        print(settings.__dict__)

    def do_stop(self, arg):
        'Stop sending emails'
        event.set()

    def do_bye(self, arg):
        'Exit the shell'
        print('Thank you for using Bulk Mailer')
        return True

    def precmd(self, line):
        return line.lower()


if __name__ == '__main__':
    MailerShell().cmdloop()
