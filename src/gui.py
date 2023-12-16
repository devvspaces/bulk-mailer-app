import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
from typing import Dict, Type
from threading import Event, Thread
from constant import APP_NAME
from domain.settings import settings

from domain.mail import EmailCounter, send_email
from domain.settings import BASE_DIR
from domain.validators import validate_setting
from validators import only_numbers

import logger  # noqa


try:
    from ctypes import windll  # Only exists on Windows.

    myappid = "xdevs.mailthunder.beta.version"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


class ScrollableLabel(tk.Frame):
    def __init__(self, parent, text, *args, **kwargs):
        super().__init__(parent)
        self.canvas = tk.Canvas(self)
        self.frame = ttk.Frame(self.canvas)
        self.vsb = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(
            (4, 4), window=self.frame, anchor="nw", tags="self.frame")

        self.frame.bind("<Configure>", self.on_frame_configure)

        label = ttk.Label(self.frame, text=text,
                          wraplength=450, *args, **kwargs)
        label.pack(fill="x")
        self.label = label

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class HomeWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master

        self.create_widgets()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=1, minsize=150)

        self.csv_string = ""
        self.csv_file = ""
        self.event = Event()
        self.counter = EmailCounter()

    def show(self):
        self.tkraise()
        self.pack(fill=tk.BOTH, expand=True)

    def create_widgets(self):
        right_frame = tk.Frame(self)
        right_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        subject_lbl = tk.Label(right_frame, text="Subject")
        subject_entry = tk.Entry(
            right_frame,
            borderwidth=10,
            relief=tk.FLAT,
        )
        body_lbl = tk.Label(right_frame, text="Body", pady=10)
        body_text = tk.Text(right_frame, borderwidth=10, relief=tk.FLAT, font=(
            "Arial", 10))
        sender_lbl = tk.Label(right_frame, text="Sender")
        sender_entry = tk.Entry(
            right_frame,
            borderwidth=10,
            relief=tk.FLAT,
        )
        sender_entry.insert(0, settings.EMAIL_USERNAME or '')

        subject_lbl.grid(row=0, column=0, sticky="w")
        subject_entry.grid(row=1, column=0, sticky="we", pady=10)
        sender_lbl.grid(row=2, column=0, sticky="w")
        sender_entry.grid(row=3, column=0, sticky="we", pady=10)
        body_lbl.grid(row=4, column=0, sticky="w")
        body_text.grid(row=5, column=0, sticky="w", pady=10)

        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        email_lbl = tk.Label(left_frame, text="Select Recipients")
        import_csv_btn = tk.Button(
            left_frame, text="Import CSV", command=self.select_file
        )
        paste_emails_btn = tk.Button(
            left_frame, text="Paste Emails", command=self.open_paste_window
        )
        send_lbl = tk.Label(left_frame, text="Send")
        send_btn = tk.Button(left_frame, text="Send", command=self.send_email)
        sent_lbl = tk.Label(
            left_frame, text="SENT 0 / 0", font=("Arial", 11, "bold"))
        self.sent_lbl = sent_lbl

        email_lbl.grid(row=0, column=0, sticky="w", pady=5)
        import_csv_btn.grid(row=1, column=0, sticky="we")
        paste_emails_btn.grid(row=2, column=0, sticky="we", pady=5)
        send_lbl.grid(row=3, column=0, sticky="w", pady=10)
        send_btn.grid(row=4, column=0, sticky="we")
        sent_lbl.grid(row=5, column=0, sticky="w", pady=50)

        self.subject = subject_entry
        self.body = body_text
        self.sender = sender_entry

    def open_paste_window(self):
        top = tk.Toplevel(self)
        top.title("Paste Emails")
        top.geometry("600x400")

        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        text = tk.Text(top)
        btn = tk.Button(top, text="Save",
                        command=lambda: self.save_paste(text))

        text.grid(row=0, column=0, sticky="nsew")
        btn.grid(row=1, column=0, sticky="we")

    def save_paste(self, text: tk.Text):
        self.csv_string = text.get("1.0", tk.END)
        text.delete("1.0", tk.END)
        text.master.destroy()

    def select_file(self):
        filename = askopenfilename(
            title="Select a CSV file",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if filename:
            self.csv_file = filename
        else:
            messagebox.showerror("Error", "No file selected")

    def validate_settings(self):
        errors = validate_setting()
        if errors:
            for error in errors:
                messagebox.showerror("Error", error)
            return False
        return True

    def send_email(self):
        if not self.validate_settings():
            return

        subject = self.subject.get()
        message = self.body.get("1.0", tk.END).strip()
        sender = self.sender.get()

        if not subject:
            messagebox.showerror("Error", "Please provide a subject")
            return

        if not message:
            messagebox.showerror("Error", "Please provide a message")
            return

        if not self.csv_file and not self.csv_string:
            messagebox.showerror(
                "Error", "Please select a CSV file or paste emails")
            return

        csv_file = self.csv_file or None
        csv_string = self.csv_string or None

        self.event.clear()
        t = Thread(
            target=send_email,
            args=(self.event,),
            kwargs={
                "csv_file": csv_file,
                "csv_string": csv_string,
                "subject": subject,
                "message": message,
                "counter": self.counter,
                "sender": sender,
            },
            daemon=True
        )
        t.start()

        self.master.after(100, self.check_event)

    def check_event(self):

        # Update the sent label
        self.sent_lbl["text"] = f"SENT {self.counter} / {self.counter.get_total()}"

        if self.event.is_set():
            messagebox.showinfo("Success", "Finished sending emails")
        else:
            self.master.after(100, self.check_event)


class SettingsWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def show(self):
        self.tkraise()
        self.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_widgets(self):
        label = tk.Label(self, text="Settings", font=("Arial", 16))
        label.pack(side="top", pady=10)

        form_frm = tk.Frame(self)
        form_frm.pack(fill=tk.BOTH, expand=True)
        form_frm.columnconfigure(0, weight=1)

        host_lbl = tk.Label(form_frm, text="Host")
        host_entry = tk.Entry(form_frm, borderwidth=10, relief=tk.FLAT)
        port_lbl = tk.Label(form_frm, text="Port")
        port_entry = tk.Entry(form_frm, borderwidth=10, relief=tk.FLAT)
        username_lbl = tk.Label(form_frm, text="Username")
        username_entry = tk.Entry(form_frm, borderwidth=10, relief=tk.FLAT)
        password_lbl = tk.Label(form_frm, text="Password")
        password_entry = tk.Entry(form_frm, borderwidth=10, relief=tk.FLAT)
        wait_time_lbl = tk.Label(form_frm, text="Wait Time")
        wait_time_entry = tk.Entry(form_frm, borderwidth=10, relief=tk.FLAT)
        save_btn = tk.Button(form_frm, text="Save", command=self.save)

        # Set values from settings
        host_entry.insert(0, settings.EMAIL_HOST or '')
        port_entry.insert(0, settings.EMAIL_PORT or '')
        username_entry.insert(0, settings.EMAIL_USERNAME or '')
        password_entry.insert(0, settings.EMAIL_PASSWORD or '')
        wait_time_entry.insert(0, settings.WAIT_TIME or '')

        # Add validations
        port_entry.config(validate="key", validatecommand=(
            port_entry.register(only_numbers), "%S"))
        wait_time_entry.config(validate="key", validatecommand=(
            wait_time_entry.register(only_numbers), "%S"))

        host_lbl.grid(row=0, column=0, sticky="w")
        host_entry.grid(row=1, column=0, sticky="we", pady=5)
        port_lbl.grid(row=2, column=0, sticky="w")
        port_entry.grid(row=3, column=0, sticky="we", pady=5)
        username_lbl.grid(row=4, column=0, sticky="w")
        username_entry.grid(row=5, column=0, sticky="we", pady=5)
        password_lbl.grid(row=6, column=0, sticky="w")
        password_entry.grid(row=7, column=0, sticky="we", pady=5)
        wait_time_lbl.grid(row=8, column=0, sticky="w")
        wait_time_entry.grid(row=9, column=0, sticky="we", pady=5)
        save_btn.grid(row=10, column=0, sticky="we", pady=5)

        self.host = host_entry
        self.port = port_entry
        self.username = username_entry
        self.password = password_entry
        self.wait_time = wait_time_entry

    def save(self):
        settings.EMAIL_HOST = self.host.get()
        settings.EMAIL_PORT = int(self.port.get() or 0)
        settings.EMAIL_USERNAME = self.username.get()
        settings.EMAIL_PASSWORD = self.password.get()
        settings.WAIT_TIME = int(self.wait_time.get() or 0)
        messagebox.showinfo("Success", "Settings saved")


class LogsWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def show(self):
        self.tkraise()
        self.pack(fill=tk.BOTH, expand=True)

    def read_logs(self):
        with open(BASE_DIR / "mailer.log") as f:
            return f.read()

    def create_widgets(self):
        label = tk.Label(self, text="Logs", font=("Arial", 16))
        label.pack(side="top", pady=10)

        frm = tk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text = self.read_logs()

        logs_lbl = ScrollableLabel(
            frm, text=text, anchor="w",
            justify="left", font=("Arial", 10),
        )
        logs_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.logs_lbl = logs_lbl
        self.master.after(100, self.update_logs, text)

    def update_logs(self, text):
        text = self.read_logs()
        self.logs_lbl.label["text"] = text
        self.logs_lbl.canvas.yview_moveto(1)
        self.master.after(100, self.update_logs, text)


class MainWindow(tk.Frame):
    def __init__(self, master: Type[tk.Tk] = None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)
        self.create_widgets()

        self.current_frame: Type[tk.Frame] = None
        self.routes: Dict[tk.Frame, Type[tk.Frame]] = {}

        # Add all frames
        self.add_frame(HomeWindow)
        self.add_frame(SettingsWindow)
        self.add_frame(LogsWindow)

        # Show home frame
        self.open_frame(HomeWindow)()

    def add_frame(self, frame_class: Type[tk.Frame]):
        frame = frame_class(self)
        self.routes[frame_class] = frame

    def open_frame(self, frame_class: Type[tk.Frame]):
        def _open_frame():
            if self.current_frame:
                self.current_frame.forget()
            if frame_class not in self.routes:
                self.routes[frame_class] = frame_class(self)
            self.routes[frame_class].show()
            self.current_frame = self.routes[frame_class]

        return _open_frame

    def create_widgets(self):
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, ipadx=10, ipady=10)
        home_btn = tk.Button(
            top_frame, text="Home", command=self.open_frame(HomeWindow)
        )
        home_btn.pack(side=tk.LEFT, padx=10)

        settings_btn = tk.Button(
            top_frame, text="Settings", command=self.open_frame(SettingsWindow)
        )
        settings_btn.pack(side=tk.LEFT, padx=10)

        logs_btn = tk.Button(
            top_frame, text="Logs", command=self.open_frame(LogsWindow)
        )
        logs_btn.pack(side=tk.LEFT, padx=10)


root = tk.Tk()
root.iconbitmap(BASE_DIR / "icons" / "icon.ico")
root.geometry("800x600")
root.title(APP_NAME)
root.resizable(False, False)
main = MainWindow(root)
root.mainloop()
