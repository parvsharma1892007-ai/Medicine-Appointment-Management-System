"""
MedCare+ - Medicine & Appointment Management System
A single-file Tkinter application rebuilt from fragmented code into a
working, runnable program.

Run with:  python medcare_plus.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import sys
import shutil
from datetime import datetime, timedelta

# winsound is Windows-only; import safely so the app still runs on other OS too
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False

# Pillow is needed to preview uploaded photos inside the app. Import safely so
# the app still runs (minus the live preview) if it isn't installed.
try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

# Twilio is needed to send real SMS reminders. Import safely so the app still
# runs (minus SMS) if it isn't installed or configured.
try:
    from twilio.rest import Client as _TwilioClient
    _HAS_TWILIO = True
except ImportError:
    _HAS_TWILIO = False


def beep_alert():
    """Play a beep sound. Uses winsound on Windows, terminal bell on other OS."""
    try:
        if _HAS_WINSOUND:
            winsound.Beep(1000, 600)  # frequency=1000Hz, duration=600ms
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        # Never let a beep failure crash the app
        pass

# ================= Config / Theme =================
BG_DARK = "#0B1E2D"
BG_MID = "#102A3E"
ACCENT = "#00C6FF"
ACCENT2 = "#1E90FF"
GOLD = "#FFD700"
DANGER = "#E74C3C"
TEXT_LIGHT = "#B0C4DE"

MEDICINE_FILE = "medicine_data.json"
APPOINTMENT_FILE = "appointment_data.json"
USERS_FILE = "users_data.json"
BACKUP_MEDICINE_FILE = "backup_medicine.json"
BACKUP_APPOINTMENT_FILE = "backup_appointment.json"
PHOTOS_DIR = "medicine_photos"

# ---- SMS Reminder Configuration ----
# To enable real, real-time SMS alerts, create a free Twilio account at
# https://www.twilio.com, grab your Account SID, Auth Token, and a Twilio
# phone number, and paste them in below. Leaving these blank simply disables
# SMS sending — the rest of the app (beep + popup reminders) keeps working.
TWILIO_ACCOUNT_SID = ""   # e.g. "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = ""    # your Twilio Auth Token
TWILIO_FROM_NUMBER = ""   # your Twilio number, e.g. "+15551234567"


# ================= Data Helpers =================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def mirror_backup(backup_path, data):
    """Automatically keep the backup file in sync every time a record is
    added, edited, or deleted in the Medicine or Appointment sections — so
    a backup always exists without the user needing to click Backup manually."""
    try:
        save_json(backup_path, data)
    except OSError:
        pass


def send_sms_reminder(to_number, message):
    """Send a real-time SMS via Twilio. Safely does nothing (returns False)
    if Twilio isn't installed or TWILIO_* credentials above aren't filled in,
    so the app keeps working normally without SMS configured."""
    if not (_HAS_TWILIO and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
        return False
    if not to_number:
        return False
    try:
        client = _TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(body=message, from_=TWILIO_FROM_NUMBER, to=to_number)
        return True
    except Exception as e:
        print(f"SMS send failed: {e}")
        return False


# ================= Reusable Widgets =================
def styled_button(parent, text, command, color=ACCENT, fg="white", width=15):
    return tk.Button(
        parent,
        text=text,
        command=command,
        bg=color,
        fg=fg,
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        width=width,
        cursor="hand2",
    )


def entry_field(parent, width=30):
    var = tk.StringVar()
    entry = tk.Entry(parent, textvariable=var, width=width, font=("Segoe UI", 11))
    return entry, var


def field_row(parent, label_text):
    row = tk.Frame(parent, bg=BG_MID)
    row.pack(fill="x", pady=10)

    tk.Label(
        row,
        text=label_text,
        bg=BG_MID,
        fg="white",
        font=("Segoe UI", 12, "bold"),
        width=15,
        anchor="w",
    ).pack(side="left", padx=10)

    entry, var = entry_field(row, width=30)
    entry.pack(side="left", padx=10)

    return entry, var


def add_topbar(frame, master, current_user=""):
    top = tk.Frame(frame, bg=BG_DARK)
    top.pack(fill="x")
    tk.Label(
        top,
        text=f"Logged in as: {current_user}",
        bg=BG_DARK,
        fg=TEXT_LIGHT,
        font=("Segoe UI", 10),
    ).pack(side="right", padx=10, pady=5)


def add_status_bar(root):
    status = tk.Label(root, text="Ready", bd=1, relief=tk.SUNKEN, anchor="w")
    status.pack(side="bottom", fill="x")
    return status


def add_footer(frame, text, color=ACCENT):
    footer = tk.Frame(frame, bg=color, height=4)
    footer.pack(fill="x", side="bottom")
    tk.Label(
        frame, text=text, bg=BG_DARK, fg="white", font=("Segoe UI", 9)
    ).pack(side="bottom", pady=4)


def show_about():
    win = tk.Toplevel()
    win.title("About Developer")
    win.geometry("400x300")
    win.configure(bg=BG_DARK)

    tk.Label(
        win, text="MedCare+", font=("Segoe UI", 22, "bold"), bg=BG_DARK, fg=ACCENT
    ).pack(pady=15)

    tk.Label(
        win,
        text="Developed By\nParv Sharma",
        font=("Segoe UI", 14),
        bg=BG_DARK,
        fg="white",
    ).pack()

    tk.Label(
        win, text="Python | Tkinter | JSON", bg=BG_DARK, fg=TEXT_LIGHT
    ).pack(pady=10)


def backup():
    """Manual full backup (in addition to the automatic per-record backup
    that now runs every time a Medicine or Appointment record is saved)."""
    try:
        shutil.copy(MEDICINE_FILE, BACKUP_MEDICINE_FILE)
        shutil.copy(APPOINTMENT_FILE, BACKUP_APPOINTMENT_FILE)
        messagebox.showinfo("Backup", "Backup Created Successfully")
    except FileNotFoundError:
        messagebox.showerror("Backup", "No data files found to back up yet.")


def restore():
    try:
        shutil.copy(BACKUP_MEDICINE_FILE, MEDICINE_FILE)
        shutil.copy(BACKUP_APPOINTMENT_FILE, APPOINTMENT_FILE)
        messagebox.showinfo("Restore", "Backup Restored")
    except FileNotFoundError:
        messagebox.showerror("Restore", "No backup files found.")


def print_report():
    messagebox.showinfo("Print", "Report Sent To Printer")


# ================= Splash Screen =================
class Splash(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("500x300")
        self.configure(bg=BG_DARK)
        self.overrideredirect(True)

        # center the splash window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 250
        y = (self.winfo_screenheight() // 2) - 150
        self.geometry(f"500x300+{x}+{y}")

        tk.Label(
            self,
            text="🏥 MedCare+",
            font=("Segoe UI", 30, "bold"),
            bg=BG_DARK,
            fg=ACCENT,
        ).pack(expand=True)

        self.after(1500, self.destroy)


# ================= Login Screen =================
class LoginScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.master = master

        tk.Label(
            self,
            text="🏥 MedCare+ Login",
            bg=BG_DARK,
            fg=ACCENT,
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=30)

        card = tk.Frame(
            self, bg=BG_MID, highlightbackground=ACCENT, highlightthickness=2
        )
        card.pack(padx=40, pady=20, fill="x")

        self.phone_entry, self.phone_var = field_row(card, "Phone")

        pass_row = tk.Frame(card, bg=BG_MID)
        pass_row.pack(fill="x", pady=10)
        tk.Label(
            pass_row,
            text="Password",
            bg=BG_MID,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left", padx=10)
        self.password_var = tk.StringVar()
        tk.Entry(
            pass_row, textvariable=self.password_var, show="*", width=30, font=("Segoe UI", 11)
        ).pack(side="left", padx=10)

        nav_frame = tk.Frame(card, bg=BG_MID)
        nav_frame.pack(pady=10)

        tk.Button(
            nav_frame,
            text="❌ Exit",
            font=("Segoe UI", 11, "bold"),
            bg="#607D8B",
            fg="white",
            relief="flat",
            width=12,
            cursor="hand2",
            command=self.master.destroy,
        ).pack(side="left", padx=10)

        tk.Button(
            nav_frame,
            text="Login ➡",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT2,
            fg="white",
            relief="flat",
            width=12,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left", padx=10)

        # ---- Register link ----
        register_frame = tk.Frame(self, bg=BG_DARK)
        register_frame.pack(pady=10)

        tk.Label(
            register_frame,
            text="Don't have an account?",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=5)

        tk.Button(
            register_frame,
            text="📝 Register",
            font=("Segoe UI", 10, "bold"),
            bg=GOLD,
            fg=BG_DARK,
            relief="flat",
            cursor="hand2",
            command=self.master._show_register,
        ).pack(side="left", padx=5)

    def _submit(self):
        phone = self.phone_var.get().strip()
        password = self.password_var.get()

        if not phone or not password:
            messagebox.showwarning("Missing Info", "Please enter phone and password.")
            return

        users = load_json(USERS_FILE)
        match = next((u for u in users if u.get("phone") == phone), None)

        if match is None:
            messagebox.showerror("Login Failed", "No account found with this phone number.")
            return

        if match.get("password") != password:
            messagebox.showerror("Login Failed", "Incorrect password.")
            return

        self.destroy()
        self.master._show_welcome(match.get("name"), match.get("phone"), match.get("age"))


# ================= Register Screen =================
class RegisterScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.master = master

        tk.Label(
            self,
            text="📝 Create an Account",
            bg=BG_DARK,
            fg=ACCENT,
            font=("Segoe UI", 26, "bold"),
        ).pack(pady=30)

        card = tk.Frame(
            self, bg=BG_MID, highlightbackground=ACCENT, highlightthickness=2
        )
        card.pack(padx=40, pady=20, fill="x")

        self.name_entry, self.name_var = field_row(card, "Name")
        self.phone_entry, self.phone_var = field_row(card, "Phone")
        self.age_entry, self.age_var = field_row(card, "Age")

        pass_row = tk.Frame(card, bg=BG_MID)
        pass_row.pack(fill="x", pady=10)
        tk.Label(
            pass_row,
            text="Password",
            bg=BG_MID,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left", padx=10)
        self.password_var = tk.StringVar()
        tk.Entry(
            pass_row, textvariable=self.password_var, show="*", width=30, font=("Segoe UI", 11)
        ).pack(side="left", padx=10)

        confirm_row = tk.Frame(card, bg=BG_MID)
        confirm_row.pack(fill="x", pady=10)
        tk.Label(
            confirm_row,
            text="Confirm Password",
            bg=BG_MID,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left", padx=10)
        self.confirm_var = tk.StringVar()
        tk.Entry(
            confirm_row, textvariable=self.confirm_var, show="*", width=30, font=("Segoe UI", 11)
        ).pack(side="left", padx=10)

        nav_frame = tk.Frame(card, bg=BG_MID)
        nav_frame.pack(pady=10)

        tk.Button(
            nav_frame,
            text="⬅ Back to Login",
            font=("Segoe UI", 11, "bold"),
            bg="#607D8B",
            fg="white",
            relief="flat",
            width=15,
            cursor="hand2",
            command=self.master._show_login,
        ).pack(side="left", padx=10)

        tk.Button(
            nav_frame,
            text="Register ✔",
            font=("Segoe UI", 11, "bold"),
            bg=ACCENT2,
            fg="white",
            relief="flat",
            width=15,
            cursor="hand2",
            command=self._submit,
        ).pack(side="left", padx=10)

    def _submit(self):
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        age = self.age_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not name or not phone or not age or not password or not confirm:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        if not age.isdigit():
            messagebox.showwarning("Invalid Age", "Age must be a number.")
            return

        if not phone.isdigit() or len(phone) < 7:
            messagebox.showwarning("Invalid Phone", "Please enter a valid phone number.")
            return

        if password != confirm:
            messagebox.showwarning("Password Mismatch", "Passwords do not match.")
            return

        users = load_json(USERS_FILE)

        if any(u.get("phone") == phone for u in users):
            messagebox.showerror("Account Exists", "An account with this phone number already exists.")
            return

        users.append({"name": name, "phone": phone, "age": age, "password": password})
        save_json(USERS_FILE, users)

        messagebox.showinfo("Success", "Account created successfully! Please log in.")
        self.master._show_login()


# ================= Welcome Screen =================
class WelcomeScreen(tk.Frame):
    def __init__(self, master, name, phone, age, on_continue):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill="both", expand=True)

        self.master = master
        self.on_continue = on_continue

        add_topbar(self, master, current_user=name)

        tk.Label(
            self,
            text="🏥 Welcome to MedCare+",
            bg=BG_DARK,
            fg=ACCENT,
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=20)

        card = tk.Frame(
            self, bg=BG_MID, highlightbackground=ACCENT, highlightthickness=2
        )
        card.pack(padx=40, pady=20, fill="x")

        tk.Label(
            card,
            text=f"👤 Name : {name}",
            bg=BG_MID,
            fg="white",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=10)

        tk.Label(
            card, text=f"📱 Mobile : {phone}", bg=BG_MID, fg="white", font=("Segoe UI", 14)
        ).pack()

        tk.Label(
            card, text=f"🎂 Age : {age}", bg=BG_MID, fg="white", font=("Segoe UI", 14)
        ).pack(pady=10)

        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(pady=25)

        tk.Button(
            btn_frame,
            text="⬅ Back",
            width=12,
            bg="#607D8B",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=lambda: master._show_login(),
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Continue ➡",
            width=15,
            bg=ACCENT2,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=lambda: self.on_continue(name, phone, age),
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="❌ Exit",
            width=12,
            bg="red",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=master.destroy,
        ).pack(side="left", padx=10)


# ================= Dashboard (Sidebar + Pages) =================
class Dashboard(tk.Frame):
    def __init__(self, master, name, phone, age):
        super().__init__(master, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.master = master
        self.name = name
        self.phone = phone
        self.age = age

        self.content_area = None
        self._build_sidebar()
        self._build_content_area()
        self.show_home()

    def _build_sidebar(self):
        main_frame = tk.Frame(self, bg=BG_DARK)
        main_frame.pack(fill="both", expand=True)
        self.main_frame = main_frame

        sidebar = tk.Frame(main_frame, bg="#08131F", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="🏥 MedCare+", bg="#08131F", fg=ACCENT, font=("Segoe UI", 18, "bold")
        ).pack(pady=20)

        tk.Label(
            sidebar, text=f"👤 {self.name}", bg="#08131F", fg="white", font=("Segoe UI", 11)
        ).pack(pady=5)

        styled_button(sidebar, "🏠 Home", self.show_home, color=ACCENT, width=18).pack(pady=5)
        styled_button(
            sidebar, "💊 Medicines", self.show_medicines, color=ACCENT2, fg="white", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "📅 Appointments", self.show_appointments, color=ACCENT2, fg="white", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "⚖ BMI", self.show_bmi, color=GOLD, fg="black", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "💾 Backup", backup, color=ACCENT, fg="white", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "♻ Restore", restore, color=ACCENT, fg="white", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "ℹ About", show_about, color=GOLD, fg=BG_DARK, width=18
        ).pack(pady=5)

        tk.Frame(sidebar, bg="#08131F").pack(expand=True)

        styled_button(
            sidebar, "⬅ Back", lambda: self.master._show_login(), color="#607D8B", fg="white", width=18
        ).pack(pady=5)
        styled_button(
            sidebar, "🚪 Logout", self.logout, color=DANGER, fg="white", width=18
        ).pack(pady=5)

    def _build_content_area(self):
        self.content_area = tk.Frame(self.main_frame, bg=BG_DARK)
        self.content_area.pack(side="left", fill="both", expand=True)

    def _clear_content(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.master._show_login()

    # ---------- Pages ----------
    def show_home(self):
        self._clear_content()
        tk.Label(
            self.content_area,
            text=f"Welcome back, {self.name}!",
            bg=BG_DARK,
            fg=ACCENT,
            font=("Segoe UI", 20, "bold"),
        ).pack(pady=40)
        tk.Label(
            self.content_area,
            text="Use the sidebar to manage medicines, appointments, or check your BMI.",
            bg=BG_DARK,
            fg=TEXT_LIGHT,
            font=("Segoe UI", 11),
        ).pack()

    def show_medicines(self):
        self._clear_content()
        MedicinePage(self.content_area, self.name)

    def show_appointments(self):
        self._clear_content()
        AppointmentPage(self.content_area, self.name)

    def show_bmi(self):
        self._clear_content()
        BMIPage(self.content_area)


# ================= Medicine Page =================
class MedicinePage(tk.Frame):
    def __init__(self, parent, name):
        super().__init__(parent, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.name = name
        self.data = load_json(MEDICINE_FILE)
        self.editing_index = None
        self.photo_path = None  # path to the currently uploaded/selected patient photo

        # ---- Nav bar ----
        nav = tk.Frame(self, bg=BG_DARK)
        nav.pack(fill="x", padx=10, pady=5)

        styled_button(nav, "🧹 Clear Form", self._cancel_edit, color=GOLD, fg=BG_DARK, width=15).pack(
            side="left", padx=5
        )

        # ---- Form ----
        form = tk.Frame(self, bg=BG_MID, highlightbackground=ACCENT, highlightthickness=1)
        form.pack(fill="x", padx=10, pady=5)

        self.patient_entry, self.patient_var = field_row(form, "Patient Name")
        self.age_entry, self.age_var = field_row(form, "Age")
        self.disease_entry, self.disease_var = field_row(form, "Disease")
        self.medicine_entry, self.medicine_var = field_row(form, "Medicine")
        self.time_entry, self.time_var = field_row(form, "Time")

        # ---- Photo upload + live preview ----
        photo_row = tk.Frame(form, bg=BG_MID)
        photo_row.pack(fill="x", pady=10)

        tk.Label(
            photo_row,
            text="Photo",
            bg=BG_MID,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left", padx=10)

        self.photo_thumb_label = tk.Label(
            photo_row, text="No Photo", bg=BG_MID, fg=TEXT_LIGHT, font=("Segoe UI", 9),
            width=8, height=3,
        )
        self.photo_thumb_label.pack(side="left", padx=10)

        styled_button(photo_row, "📷 Upload Photo", self._upload_photo, color=ACCENT, width=15).pack(
            side="left", padx=5
        )
        styled_button(photo_row, "🖼 View Photo", self._view_photo, color=ACCENT2, width=15).pack(
            side="left", padx=5
        )

        btn_row = tk.Frame(form, bg=BG_MID)
        btn_row.pack(pady=10)
        styled_button(btn_row, "💾 Save", self._save_record, color=ACCENT2, width=15).pack(
            side="left", padx=5
        )
        styled_button(btn_row, "🗑 Delete", self._delete_record, color=DANGER, width=15).pack(
            side="left", padx=5
        )

        # ---- Search ----
        search_frame = tk.Frame(self, bg=BG_DARK)
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="🔍 Search Patient", bg=BG_DARK, fg="white").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._load_table())
        tk.Entry(search_frame, textvariable=self.search_var).pack(side="left", padx=5)

        # ---- Table ----
        columns = ("patient_name", "age", "disease", "medicine", "time")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self._edit_selected)

        self.record_label = tk.Label(
            self, text="📋 Total Records : 0", bg=BG_DARK, fg=GOLD, font=("Segoe UI", 11, "bold")
        )
        self.record_label.pack(pady=5)

        tk.Label(
            self, text="💡 Double Click any record to Edit.", bg=BG_DARK, fg=TEXT_LIGHT, font=("Segoe UI", 10)
        ).pack(pady=5)

        add_footer(self, "MedCare+ Medicine Management System", ACCENT)

        self._load_table()
        self._refresh_photo_preview()

    def _filtered_data(self):
        query = self.search_var.get().lower().strip()
        if not query:
            return self.data
        return [m for m in self.data if query in m.get("patient_name", "").lower()]

    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        data = self._filtered_data()

        for m in data:
            self.tree.insert(
                "",
                "end",
                values=(
                    m.get("patient_name"),
                    m.get("age"),
                    m.get("disease"),
                    m.get("medicine"),
                    m.get("time"),
                ),
            )

        self.record_label.config(text=f"📋 Total Records : {len(data)}")

    def _upload_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not path:
            return
        try:
            os.makedirs(PHOTOS_DIR, exist_ok=True)
            ext = os.path.splitext(path)[1].lower() or ".png"
            dest_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
            dest_path = os.path.join(PHOTOS_DIR, dest_name)
            shutil.copy(path, dest_path)
        except OSError as e:
            messagebox.showerror("Upload Failed", f"Could not save photo: {e}")
            return

        self.photo_path = dest_path
        self._refresh_photo_preview()
        messagebox.showinfo("Success", "Photo Uploaded Successfully")

    def _refresh_photo_preview(self):
        """Show a small thumbnail of the currently attached photo so the user
        can actually see what was uploaded, instead of it just disappearing."""
        if not self.photo_path or not os.path.exists(self.photo_path):
            self.photo_thumb_label.config(image="", text="No Photo", fg=TEXT_LIGHT)
            self.photo_thumb_label.image = None
            return

        if not _HAS_PIL:
            self.photo_thumb_label.config(image="", text="Saved\n(install\nPillow)", fg=TEXT_LIGHT)
            self.photo_thumb_label.image = None
            return

        try:
            img = Image.open(self.photo_path)
            img.thumbnail((60, 60))
            photo = ImageTk.PhotoImage(img)
            self.photo_thumb_label.config(image=photo, text="")
            self.photo_thumb_label.image = photo  # keep a reference so it isn't garbage-collected
        except Exception:
            self.photo_thumb_label.config(image="", text="Preview\nerror", fg=DANGER)
            self.photo_thumb_label.image = None

    def _view_photo(self):
        if not self.photo_path or not os.path.exists(self.photo_path):
            messagebox.showinfo("No Photo", "No photo has been uploaded for this record yet.")
            return

        if not _HAS_PIL:
            messagebox.showinfo(
                "Photo Saved",
                f"The photo is saved at:\n{self.photo_path}\n\nInstall Pillow (pip install Pillow) to preview it inside the app.",
            )
            return

        win = tk.Toplevel(self)
        win.title("Patient Photo")
        win.configure(bg=BG_DARK)
        try:
            img = Image.open(self.photo_path)
            img.thumbnail((500, 500))
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(win, image=photo, bg=BG_DARK)
            lbl.image = photo  # keep a reference
            lbl.pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(win, text=f"Could not open photo: {e}", bg=BG_DARK, fg=DANGER).pack(padx=20, pady=20)

    def _save_record(self):
        record = {
            "patient_name": self.patient_var.get().strip(),
            "age": self.age_var.get().strip(),
            "disease": self.disease_var.get().strip(),
            "medicine": self.medicine_var.get().strip(),
            "time": self.time_var.get().strip(),
            "photo_path": self.photo_path,
        }

        if not record["patient_name"]:
            messagebox.showwarning("Missing Info", "Patient name is required.")
            return

        if self.editing_index is not None:
            self.data[self.editing_index] = record
        else:
            self.data.append(record)

        save_json(MEDICINE_FILE, self.data)
        mirror_backup(BACKUP_MEDICINE_FILE, self.data)  # auto-backup every save
        self._cancel_edit()
        self._load_table()

    def _delete_record(self):
        if self.editing_index is None:
            messagebox.showwarning("No Selection", "Select a record from the table first.")
            return
        del self.data[self.editing_index]
        save_json(MEDICINE_FILE, self.data)
        mirror_backup(BACKUP_MEDICINE_FILE, self.data)  # keep backup in sync after delete too
        self._cancel_edit()
        self._load_table()

    def _edit_selected(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]

        # Find matching record by patient name + time (simple match)
        for i, m in enumerate(self.data):
            if str(m.get("patient_name")) == str(values[0]) and str(m.get("time")) == str(values[4]):
                self.editing_index = i
                self.patient_var.set(m.get("patient_name", ""))
                self.age_var.set(m.get("age", ""))
                self.disease_var.set(m.get("disease", ""))
                self.medicine_var.set(m.get("medicine", ""))
                self.time_var.set(m.get("time", ""))
                self.photo_path = m.get("photo_path")
                self._refresh_photo_preview()
                break

    def _cancel_edit(self):
        self.editing_index = None
        self.patient_var.set("")
        self.age_var.set("")
        self.disease_var.set("")
        self.medicine_var.set("")
        self.time_var.set("")
        self.photo_path = None
        self._refresh_photo_preview()


# ================= Appointment Page =================
class AppointmentPage(tk.Frame):
    def __init__(self, parent, name):
        super().__init__(parent, bg=BG_DARK)
        self.pack(fill="both", expand=True)
        self.name = name
        self.data = load_json(APPOINTMENT_FILE)
        self.editing_index = None
        self._alerted_keys = set()  # tracks appointments already beeped, avoid repeat beeps

        nav = tk.Frame(self, bg=BG_DARK)
        nav.pack(fill="x", padx=10, pady=5)
        styled_button(nav, "🧹 Clear Form", self._cancel_edit, color=GOLD, fg=BG_DARK, width=15).pack(
            side="left", padx=5
        )

        form = tk.Frame(self, bg=BG_MID, highlightbackground=ACCENT2, highlightthickness=1)
        form.pack(fill="x", padx=10, pady=5)

        self.patient_entry, self.patient_var = field_row(form, "Patient Name")
        self.phone_entry, self.phone_var = field_row(form, "Phone (+countrycode)")
        self.date_entry, self.date_var = field_row(form, "Date (YYYY-MM-DD)")
        self.time_entry, self.time_var = field_row(form, "Time (HH:MM)")
        self.doctor_entry, self.doctor_var = field_row(form, "Doctor")

        btn_row = tk.Frame(form, bg=BG_MID)
        btn_row.pack(pady=10)
        styled_button(btn_row, "💾 Save", self._save_record, color=ACCENT2, width=15).pack(
            side="left", padx=5
        )
        styled_button(btn_row, "🗑 Delete", self._delete_record, color=DANGER, width=15).pack(
            side="left", padx=5
        )

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._load_table())
        search_frame = tk.Frame(self, bg=BG_DARK)
        search_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(search_frame, text="🔍 Search Patient", bg=BG_DARK, fg="white").pack(side="left")
        tk.Entry(search_frame, textvariable=self.search_var).pack(side="left", padx=5)

        stats_frame = tk.Frame(self, bg=BG_DARK)
        stats_frame.pack(fill="x", pady=5)
        self.total_label = tk.Label(
            stats_frame, text="📅 Total Appointments : 0", bg=BG_DARK, fg=GOLD, font=("Segoe UI", 11, "bold")
        )
        self.total_label.pack(side="left", padx=10)
        self.upcoming_label = tk.Label(
            stats_frame, text="⏰ Upcoming : 0", bg=BG_DARK, fg=ACCENT2, font=("Segoe UI", 11, "bold")
        )
        self.upcoming_label.pack(side="right", padx=10)

        columns = ("patient_name", "phone", "date", "time", "doctor")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree.bind("<Double-1>", self._edit_selected)

        tk.Label(
            self,
            text="💡 Double Click any appointment to Edit.  📲 SMS reminders send automatically if a phone number is entered and Twilio is configured.",
            bg=BG_DARK, fg=TEXT_LIGHT, font=("Segoe UI", 10),
        ).pack(pady=5)

        add_footer(self, "MedCare+ Appointment Management System", ACCENT2)

        self._load_table()
        self._check_reminders()  # start 24-hour-before beep reminder loop

    def _filtered_data(self):
        query = self.search_var.get().lower().strip()
        if not query:
            return self.data
        return [m for m in self.data if query in m.get("patient_name", "").lower()]

    def _load_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        data = self._filtered_data()
        for m in data:
            self.tree.insert(
                "",
                "end",
                values=(m.get("patient_name"), m.get("phone"), m.get("date"), m.get("time"), m.get("doctor")),
            )

        total = len(data)
        upcoming = 0
        for item in data:
            try:
                dt = datetime.strptime(f"{item['date']} {item['time']}", "%Y-%m-%d %H:%M")
                if dt > datetime.now():
                    upcoming += 1
            except (KeyError, ValueError):
                pass

        self.total_label.config(text=f"📅 Total Appointments : {total}")
        self.upcoming_label.config(text=f"⏰ Upcoming : {upcoming}")

    def _check_reminders(self):
        """Runs every 60 seconds. Beeps once for any appointment whose time
        is within the next 24 hours (and hasn't already been alerted)."""
        now = datetime.now()

        for item in self.data:
            try:
                dt = datetime.strptime(f"{item['date']} {item['time']}", "%Y-%m-%d %H:%M")
            except (KeyError, ValueError):
                continue

            key = f"{item.get('patient_name')}|{item.get('date')}|{item.get('time')}"
            time_left = dt - now

            # Within next 24 hours and still in the future -> beep once
            if timedelta(seconds=0) < time_left <= timedelta(hours=24) and key not in self._alerted_keys:
                self._alerted_keys.add(key)
                beep_alert()

                reminder_text = (
                    f"Reminder: {item.get('patient_name')}'s appointment with "
                    f"{item.get('doctor', 'Doctor')} is on {item.get('date')} at {item.get('time')} "
                    f"(within 24 hours)."
                )
                messagebox.showinfo("⏰ Appointment Reminder", reminder_text)

                # Real-time SMS alert (requires TWILIO_* credentials to be
                # filled in at the top of this file, plus a phone number on
                # the appointment). Fails silently if not configured.
                sms_text = (
                    f"MedCare+ Reminder: Hi {item.get('patient_name')}, your appointment with "
                    f"{item.get('doctor', 'Doctor')} is on {item.get('date')} at {item.get('time')}."
                )
                send_sms_reminder(item.get("phone"), sms_text)

        # Re-check every 60 seconds, only while this page still exists
        if self.winfo_exists():
            self.after(60000, self._check_reminders)

    def _save_record(self):
        record = {
            "patient_name": self.patient_var.get().strip(),
            "phone": self.phone_var.get().strip(),
            "date": self.date_var.get().strip(),
            "time": self.time_var.get().strip(),
            "doctor": self.doctor_var.get().strip(),
        }

        if not record["patient_name"]:
            messagebox.showwarning("Missing Info", "Patient name is required.")
            return

        if self.editing_index is not None:
            self.data[self.editing_index] = record
        else:
            self.data.append(record)

        save_json(APPOINTMENT_FILE, self.data)
        mirror_backup(BACKUP_APPOINTMENT_FILE, self.data)  # auto-backup every save
        self._cancel_edit()
        self._load_table()

    def _delete_record(self):
        if self.editing_index is None:
            messagebox.showwarning("No Selection", "Select an appointment from the table first.")
            return
        del self.data[self.editing_index]
        save_json(APPOINTMENT_FILE, self.data)
        mirror_backup(BACKUP_APPOINTMENT_FILE, self.data)  # keep backup in sync after delete too
        self._cancel_edit()
        self._load_table()

    def _edit_selected(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = self.tree.item(selection[0])
        values = item["values"]

        for i, m in enumerate(self.data):
            if (
                str(m.get("patient_name")) == str(values[0])
                and str(m.get("date")) == str(values[2])
                and str(m.get("time")) == str(values[3])
            ):
                self.editing_index = i
                self.patient_var.set(m.get("patient_name", ""))
                self.phone_var.set(m.get("phone", ""))
                self.date_var.set(m.get("date", ""))
                self.time_var.set(m.get("time", ""))
                self.doctor_var.set(m.get("doctor", ""))
                break

    def _cancel_edit(self):
        self.editing_index = None
        self.patient_var.set("")
        self.phone_var.set("")
        self.date_var.set("")
        self.time_var.set("")
        self.doctor_var.set("")


# ================= BMI Page =================
class BMIPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_DARK)
        self.pack(fill="both", expand=True)

        tk.Label(
            self, text="⚖ BMI Calculator", bg=BG_DARK, fg=GOLD, font=("Segoe UI", 20, "bold")
        ).pack(pady=20)

        form = tk.Frame(self, bg=BG_MID, highlightbackground=GOLD, highlightthickness=1)
        form.pack(padx=40, pady=10, fill="x")

        self.weight_entry, self.weight_var = field_row(form, "Weight (kg)")
        self.height_entry, self.height_var = field_row(form, "Height (cm)")

        styled_button(form, "Calculate", self._calculate, color=GOLD, fg=BG_DARK, width=15).pack(pady=15)

        self.result_label = tk.Label(
            self, text="", bg=BG_DARK, fg="white", font=("Segoe UI", 14, "bold")
        )
        self.result_label.pack(pady=20)

    def _calculate(self):
        try:
            weight = float(self.weight_var.get())
            height_cm = float(self.height_var.get())
            height_m = height_cm / 100
            bmi = weight / (height_m ** 2)

            if bmi < 18.5:
                category = "Underweight"
            elif bmi < 25:
                category = "Normal"
            elif bmi < 30:
                category = "Overweight"
            else:
                category = "Obese"

            self.result_label.config(text=f"BMI: {bmi:.1f} ({category})")
        except (ValueError, ZeroDivisionError):
            messagebox.showwarning("Invalid Input", "Please enter valid numeric weight and height.")


# ================= Main App =================
class MedCareApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MedCare+")
        self.geometry("900x650")
        self.configure(bg=BG_DARK)

        self.status_bar = add_status_bar(self)

        self.current_frame = None
        self._show_login()

    def _clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def _show_login(self):
        self._clear_frame()
        self.current_frame = LoginScreen(self)

    def _show_register(self):
        self._clear_frame()
        self.current_frame = RegisterScreen(self)

    def _show_welcome(self, name, phone, age):
        self._clear_frame()
        self.current_frame = WelcomeScreen(self, name, phone, age, self._show_dashboard)

    def _show_dashboard(self, name, phone, age):
        self._clear_frame()
        self.current_frame = Dashboard(self, name, phone, age)


def main():
    root = tk.Tk()
    root.withdraw()  # hide the empty root window used only to host the splash

    splash = Splash(root)
    root.wait_window(splash)
    root.destroy()

    app = MedCareApp()
    app.mainloop()


if __name__ == "__main__":
    main()
