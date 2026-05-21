# 🎓 Le Schéma — School Management ERP

> **Innover - Créer - Exceller**

A complete, professional, futuristic school management desktop application built with Python and Tkinter. Features a dark-mode glassmorphism UI, full SQLite database, automatic PDF receipt generation, and role-based access control.

---

## 🚀 Quick Start

### Option 1 — Run from Source (Recommended for development)

**Windows:**
```batch
run_windows.bat
```

**Linux / macOS:**
```bash
chmod +x run_linux.sh
./run_linux.sh
```

**Manual:**
```bash
pip install -r requirements.txt
python main.py
```

### Option 2 — Download Pre-built EXE

Go to **GitHub Actions → Latest build → Artifacts** and download:
- `LeSchema-School-ERP-Windows` → `.exe` (Windows)
- `LeSchema-School-ERP-Linux` → binary (Linux)
- `LeSchema-School-ERP-macOS` → binary (macOS)

### Option 3 — Build yourself

```bash
pip install pyinstaller
pyinstaller LeSchema_SchoolERP.spec
# Output: dist/LeSchema_SchoolERP.exe
```

---

## 🔑 Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Comptable | `comptable` | `compta123` |
| Secrétaire | `secretaire` | `sec123` |

> ⚠️ Change passwords immediately after first login via Settings → User Management.

---

## ✨ Features

### 📊 Dashboard
- Real-time statistics: students, revenue, expenses, profit
- Monthly & yearly financial overview
- Quick action buttons
- Live notifications panel

### 👩‍🎓 Student Management
- Complete student profiles with photo support
- 15 class levels: PS → 2BAC
- Transport & insurance tracking
- Auto-generated student codes (STU-YYYY-XXXX)
- Search & filter functionality

### 💳 Payment System
- Monthly fees, insurance, transport payments
- **Automatic PDF receipt generation** with QR code
- Receipt numbering: REC-YYYY-XXXXXX
- Payment history with filtering
- Print receipts directly

### 👨‍💼 Employee & Teacher Management
- Full employee profiles
- Role-based categorization
- Salary management with bonuses & deductions
- Salary history tracking

### 💸 Expense Management
- Fixed & variable expense categories
- Real-time totals
- Financial analytics

### 🚌 Transport Management
- View all transport subscribers
- Bus & route management
- Transport fee tracking

### 📅 Timetable
- Visual weekly timetable grid
- Per-class schedule management
- Subject & teacher assignment

### 📁 Document Management
- Import & store any file type
- Organize by student/employee
- Quick open functionality

### 📈 Reports & Exports
- Student list PDF
- Financial report PDF
- Payment history
- Employee report

### ⚙️ Settings
- School information customization
- Financial parameters (fees, currency)
- User management (Admin only)
- Backup & restore database

### 💾 Backup System
- One-click database backup
- Timestamped backup files
- Easy restore functionality

---

## 🏗️ Project Structure

```
SchoolApp/
├── main.py                    # Main application & all UI
├── requirements.txt           # Python dependencies
├── LeSchema_SchoolERP.spec    # PyInstaller build config
├── version_info.txt           # Windows EXE version info
├── run_windows.bat            # Windows launcher
├── run_linux.sh               # Linux/macOS launcher
│
├── assets/
│   ├── school_logo.png        # School logo (PNG, 400×400)
│   └── school_logo.ico        # School icon (ICO, multi-size)
│
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   └── seed.py                # Default data seeding
│
├── utils/
│   ├── __init__.py
│   └── receipt_generator.py   # PDF receipt generator
│
├── data/
│   └── school.db              # SQLite database (auto-created)
│
├── receipts/                  # Generated PDF receipts
├── reports/                   # Generated PDF reports
├── backups/                   # Database backups
├── documents/                 # Imported documents
│
└── .github/
    └── workflows/
        └── build.yml          # GitHub Actions CI/CD
```

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `users` | Login accounts with role-based access |
| `students` | Student profiles & enrollment data |
| `payments` | All payment transactions |
| `employees` | Staff & teacher records |
| `salaries` | Monthly salary payments |
| `expenses` | School expenses |
| `buses` | Transport buses |
| `schedules` | Class timetables |
| `documents` | Document registry |
| `settings` | Application configuration |
| `backups` | Backup history |

---

## 🎨 UI Design

- **Theme:** Dark mode glassmorphism
- **Colors:** Orange `#FF6B00` + Blue `#4F8EF7` + Purple `#8B5CF6`
- **Font:** Segoe UI (professional ERP style)
- **Layout:** Sidebar + Navbar + Content area
- **Animations:** Smooth fade-in on login

---

## 🔧 Building the EXE (GitHub Actions)

1. Push this project to a GitHub repository
2. Go to **Actions** tab
3. The `build.yml` workflow runs automatically
4. Download the `.exe` from **Artifacts** section

Or trigger manually: **Actions → Build School Management App → Run workflow**

---

## 📋 System Requirements

| Component | Minimum |
|-----------|---------|
| OS | Windows 10+, Ubuntu 20.04+, macOS 11+ |
| Python | 3.9+ (if running from source) |
| RAM | 512 MB |
| Disk | 200 MB |
| Display | 1024×768 minimum, 1280×800 recommended |

---

## 🛠️ Dependencies

| Package | Purpose |
|---------|---------|
| `Pillow` | Image processing & logo handling |
| `reportlab` | PDF receipt & report generation |
| `qrcode` | QR codes on receipts |
| `SQLAlchemy` | Database ORM |
| `bcrypt` | Password hashing |
| `tkinter` | GUI framework (built into Python) |

---

## 📞 Support

**Le Schéma** — Innover - Créer - Exceller  
📧 contact@leschema.ma  
🌐 www.leschema.ma

---

*Built with ❤️ for Le Schéma School*
