# 🏥 MedCare+ — Medicine & Appointment Management System

MedCare+ is a desktop application built with **Python** and **Tkinter** that helps patients and caregivers manage medicines, doctor appointments, and basic health metrics — all through a clean, dark-themed GUI backed by local JSON storage.

---

## ✨ Features

### 🔐 User Accounts
- Register a new account with name, phone number, age, and password
- Login with phone number and password
- Simple JSON-based user store (`users_data.json`)

### 💊 Medicine Management
- Add, edit, delete, and search patient medicine records (patient name, age, disease, medicine, time)
- Upload a patient photo per record, with a **live thumbnail preview** in the form
- Click **View Photo** to open a full-size preview in a separate window
- Double-click any row in the table to load it into the form for editing

### 📅 Appointment Management
- Add, edit, delete, and search appointments (patient name, phone, date, time, doctor)
- Live dashboard stats: total appointments and upcoming appointments
- **Automatic reminders**: the app checks every 60 seconds and triggers a beep + popup for any appointment within the next 24 hours
- **Optional SMS reminders** via [Twilio](https://www.twilio.com) when the appointment has a phone number and Twilio credentials are configured

### ⚖ BMI Calculator
- Enter weight (kg) and height (cm) to instantly calculate BMI and category (Underweight / Normal / Overweight / Obese)

### 💾 Backup & Restore
- **Automatic backup**: every time a medicine or appointment record is saved or deleted, a mirrored backup file is written automatically
- **Manual backup/restore** buttons in the sidebar for full-file snapshots

### 🎨 UI/UX
- Custom dark, "medical-tech" themed interface (navy + cyan + gold accents)
- Animated splash screen on launch
- Sidebar navigation with Home, Medicines, Appointments, BMI, Backup, Restore, and About pages
- Status bar and page footers throughout

---

## 🧰 Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3 |
| GUI | Tkinter / ttk |
| Data Storage | JSON (flat-file, no database required) |
| Image Handling | Pillow (`PIL`) — optional |
| SMS Reminders | Twilio REST API — optional |
| Sound Alerts | `winsound` (Windows) / terminal bell (other OS) |

---

## 📦 Requirements

- Python 3.8+
- Tkinter (usually bundled with Python)

**Optional but recommended:**
```bash
pip install Pillow          # enables in-app photo previews
pip install twilio          # enables real SMS appointment reminders
```

> The app is designed to **degrade gracefully** — if Pillow or Twilio are not installed, those specific features are silently disabled and the rest of the app works normally.

---

## 🚀 Getting Started

1. Clone or download this repository
2. (Optional) Install the optional dependencies above
3. Run the app:
   ```bash
   python medcare_plus.py
   ```
4. On first use, click **Register** to create an account, then log in

### Enabling SMS Reminders (optional)
Open `medcare_plus.py` and fill in your [Twilio](https://www.twilio.com) credentials near the top of the file:
```python
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_FROM_NUMBER = "+15551234567"
```
Leave these blank to keep SMS disabled — beep and popup reminders will still work.

---

## 🗂 Project Structure

```
medcare_plus.py            # Single-file application (all classes & logic)
medicine_data.json         # Medicine records (auto-created)
appointment_data.json      # Appointment records (auto-created)
users_data.json            # Registered user accounts (auto-created)
backup_medicine.json        # Auto/manual backup of medicine records
backup_appointment.json     # Auto/manual backup of appointment records
medicine_photos/           # Uploaded patient photos (auto-created)
```

All data files are created automatically on first use — no manual setup required.

---

## 🖥 Application Flow

```
Splash Screen → Login/Register → Welcome Screen → Dashboard
                                                     ├── Home
                                                     ├── Medicines
                                                     ├── Appointments
                                                     ├── BMI Calculator
                                                     ├── Backup / Restore
                                                     └── About
```

---

## ⚠ Known Limitations

- Passwords are stored in **plain text** in `users_data.json` — this project is intended for learning/demo purposes, not production use with real patient data
- Data is stored per-machine in local JSON files (no multi-user sync or cloud storage)
- Reminder checks only run while the Appointments page's reminder loop is active during the session

## 🔮 Possible Future Enhancements

- Password hashing (e.g. `bcrypt`) instead of plain text
- Migrate from flat JSON files to SQLite for more robust data handling
- Export medicine/appointment history to PDF
- Multi-user roles (e.g. doctor vs. patient views)

---

## 🧑‍💻 Built With

Python | Tkinter | JSON

---

## 📄 License

This project is licensed under the MIT License.

```
MIT License


Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
