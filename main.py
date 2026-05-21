"""
Le Schéma - School Management System
Main Application Entry Point
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import threading

# Ensure app directory is in path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# Initialize database
from database.seed import seed_database
seed_database()

from database.models import get_session, User, Student, Payment, Employee, Salary, Expense, Setting, Backup, CLASSES
from utils.receipt_generator import generate_receipt
from datetime import datetime, date
import hashlib
import shutil
import json


# ─── COLOR PALETTE ───────────────────────────────────────────────────────────
BG_DARK       = "#0f0f1a"
BG_SIDEBAR    = "#16162a"
BG_CARD       = "#1e1e3a"
BG_CARD2      = "#252545"
ACCENT_ORANGE = "#FF6B00"
ACCENT_BLUE   = "#4F8EF7"
ACCENT_PURPLE = "#8B5CF6"
ACCENT_GREEN  = "#10B981"
ACCENT_RED    = "#EF4444"
ACCENT_YELLOW = "#F59E0B"
TEXT_PRIMARY  = "#F1F5F9"
TEXT_SECONDARY= "#94A3B8"
TEXT_MUTED    = "#475569"
BORDER_COLOR  = "#2d2d5b"
HOVER_COLOR   = "#2a2a50"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_settings():
    session = get_session()
    settings = {}
    for s in session.query(Setting).all():
        settings[s.key] = s.value
    session.close()
    return settings


def save_setting(key, value):
    session = get_session()
    s = session.query(Setting).filter_by(key=key).first()
    if s:
        s.value = str(value)
        s.updated_at = datetime.now()
    else:
        session.add(Setting(key=key, value=str(value)))
    session.commit()
    session.close()


def next_receipt_number():
    session = get_session()
    s = session.query(Setting).filter_by(key="receipt_counter").first()
    counter = int(s.value) + 1 if s else 1
    if s:
        s.value = str(counter)
        s.updated_at = datetime.now()
    else:
        session.add(Setting(key="receipt_counter", value=str(counter)))
    session.commit()
    session.close()
    year = datetime.now().year
    return f"REC-{year}-{counter:06d}"


def next_student_code():
    session = get_session()
    count = session.query(Student).count() + 1
    session.close()
    year = datetime.now().year
    return f"STU-{year}-{count:04d}"


def next_employee_code():
    session = get_session()
    count = session.query(Employee).count() + 1
    session.close()
    return f"EMP-{count:04d}"


# ─── STYLED WIDGETS ──────────────────────────────────────────────────────────

class ModernButton(tk.Button):
    def __init__(self, parent, text, command=None, color=ACCENT_ORANGE, fg=TEXT_PRIMARY,
                 width=None, height=None, font_size=10, **kwargs):
        super().__init__(
            parent, text=text, command=command,
            bg=color, fg=fg, activebackground=color,
            activeforeground=fg, relief="flat", cursor="hand2",
            font=("Segoe UI", font_size, "bold"),
            padx=16, pady=8, bd=0,
            **kwargs
        )
        if width:
            self.config(width=width)
        self._color = color
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(bg=self._lighten(self._color))

    def _on_leave(self, e):
        self.config(bg=self._color)

    def _lighten(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = min(255, r + 30)
        g = min(255, g + 30)
        b = min(255, b + 30)
        return f"#{r:02x}{g:02x}{b:02x}"


class Card(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_CARD, relief="flat", bd=0, **kwargs)


class StatCard(tk.Frame):
    def __init__(self, parent, title, value, icon, color, **kwargs):
        super().__init__(parent, bg=BG_CARD, relief="flat", bd=0, padx=20, pady=15, **kwargs)
        
        tk.Label(self, text=icon, font=("Segoe UI Emoji", 22), bg=BG_CARD, fg=color).pack(anchor="w")
        tk.Label(self, text=str(value), font=("Segoe UI", 22, "bold"), bg=BG_CARD, fg=color).pack(anchor="w")
        tk.Label(self, text=title, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        
        # Bottom accent bar
        bar = tk.Frame(self, bg=color, height=3)
        bar.pack(fill="x", side="bottom", pady=(10, 0))


class SidebarButton(tk.Frame):
    def __init__(self, parent, text, icon, command, active=False, **kwargs):
        super().__init__(parent, bg=BG_SIDEBAR, cursor="hand2", **kwargs)
        
        self._command = command
        self._active = active
        
        self._bg = ACCENT_ORANGE if active else BG_SIDEBAR
        self._fg = TEXT_PRIMARY
        
        self.config(bg=self._bg)
        
        inner = tk.Frame(self, bg=self._bg, padx=12, pady=10)
        inner.pack(fill="x")
        
        self._icon_label = tk.Label(inner, text=icon, font=("Segoe UI Emoji", 14), 
                                     bg=self._bg, fg=self._fg)
        self._icon_label.pack(side="left", padx=(0, 10))
        
        self._text_label = tk.Label(inner, text=text, font=("Segoe UI", 10, "bold" if active else "normal"),
                                     bg=self._bg, fg=self._fg, anchor="w")
        self._text_label.pack(side="left", fill="x")
        
        self._inner = inner
        
        for widget in [self, inner, self._icon_label, self._text_label]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    def _on_click(self, e):
        if self._command:
            self._command()

    def _on_enter(self, e):
        if not self._active:
            for w in [self, self._inner, self._icon_label, self._text_label]:
                w.config(bg=HOVER_COLOR)

    def _on_leave(self, e):
        if not self._active:
            for w in [self, self._inner, self._icon_label, self._text_label]:
                w.config(bg=BG_SIDEBAR)

    def set_active(self, active):
        self._active = active
        bg = ACCENT_ORANGE if active else BG_SIDEBAR
        font_weight = "bold" if active else "normal"
        for w in [self, self._inner, self._icon_label, self._text_label]:
            w.config(bg=bg)
        self._text_label.config(font=("Segoe UI", 10, font_weight))


class ModernEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0, **kwargs)
        self._placeholder = placeholder
        if placeholder:
            self.insert(0, placeholder)
            self.config(fg=TEXT_MUTED)
            self.bind("<FocusIn>", self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, e):
        if self.get() == self._placeholder:
            self.delete(0, "end")
            self.config(fg=TEXT_PRIMARY)

    def _on_focus_out(self, e):
        if not self.get():
            self.insert(0, self._placeholder)
            self.config(fg=TEXT_MUTED)

    def get_value(self):
        val = self.get()
        return "" if val == self._placeholder else val


class ModernCombobox(ttk.Combobox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(font=("Segoe UI", 10))


class StyledTreeview(ttk.Treeview):
    def __init__(self, parent, columns, headings, **kwargs):
        super().__init__(parent, columns=columns, show="headings", **kwargs)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
            background=BG_CARD, foreground=TEXT_PRIMARY,
            rowheight=32, fieldbackground=BG_CARD,
            borderwidth=0, font=("Segoe UI", 9))
        style.configure("Custom.Treeview.Heading",
            background=BG_CARD2, foreground=ACCENT_ORANGE,
            font=("Segoe UI", 9, "bold"), borderwidth=0, relief="flat")
        style.map("Custom.Treeview",
            background=[("selected", ACCENT_ORANGE)],
            foreground=[("selected", TEXT_PRIMARY)])
        
        self.configure(style="Custom.Treeview")
        
        for col, heading in zip(columns, headings):
            self.heading(col, text=heading, anchor="w")
            self.column(col, anchor="w", minwidth=60)

        self.tag_configure("odd", background=BG_CARD)
        self.tag_configure("even", background=BG_CARD2)


# ─── LOGIN SCREEN ────────────────────────────────────────────────────────────

class LoginScreen(tk.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.on_success = on_success
        self.title("Le Schéma - Connexion")
        self.geometry("480x580")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self.grab_set()
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 480) // 2
        y = (self.winfo_screenheight() - 580) // 2
        self.geometry(f"480x580+{x}+{y}")
        
        self._build_ui()
        self._animate_in()

    def _build_ui(self):
        main = tk.Frame(self, bg=BG_DARK, padx=50, pady=40)
        main.pack(fill="both", expand=True)

        # Logo
        logo_path = os.path.join(APP_DIR, "assets", "school_logo.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(logo_path).resize((120, 120), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(img)
            tk.Label(main, image=self._logo, bg=BG_DARK).pack(pady=(0, 10))
        except Exception:
            tk.Label(main, text="🎓", font=("Segoe UI Emoji", 50), bg=BG_DARK, fg=ACCENT_ORANGE).pack(pady=(0,10))

        tk.Label(main, text="Le Schéma", font=("Segoe UI", 22, "bold"),
                bg=BG_DARK, fg=ACCENT_ORANGE).pack()
        tk.Label(main, text="Innover - Créer - Exceller", font=("Segoe UI", 10),
                bg=BG_DARK, fg=TEXT_SECONDARY).pack(pady=(0, 30))

        # Form card
        form = tk.Frame(main, bg=BG_CARD, padx=30, pady=25)
        form.pack(fill="x")

        tk.Label(form, text="Connexion", font=("Segoe UI", 14, "bold"),
                bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))

        # Username
        tk.Label(form, text="Nom d'utilisateur", font=("Segoe UI", 9),
                bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        
        user_frame = tk.Frame(form, bg=BG_CARD2, padx=12, pady=2)
        user_frame.pack(fill="x", pady=(2, 12))
        tk.Label(user_frame, text="👤", font=("Segoe UI Emoji", 12), bg=BG_CARD2).pack(side="left")
        self.username_entry = tk.Entry(user_frame, bg=BG_CARD2, fg=TEXT_PRIMARY,
                                        insertbackground=TEXT_PRIMARY, relief="flat",
                                        font=("Segoe UI", 11), bd=0)
        self.username_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        self.username_entry.insert(0, "admin")

        # Password
        tk.Label(form, text="Mot de passe", font=("Segoe UI", 9),
                bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
        
        pass_frame = tk.Frame(form, bg=BG_CARD2, padx=12, pady=2)
        pass_frame.pack(fill="x", pady=(2, 16))
        tk.Label(pass_frame, text="🔒", font=("Segoe UI Emoji", 12), bg=BG_CARD2).pack(side="left")
        self.password_entry = tk.Entry(pass_frame, bg=BG_CARD2, fg=TEXT_PRIMARY,
                                        insertbackground=TEXT_PRIMARY, relief="flat",
                                        font=("Segoe UI", 11), bd=0, show="●")
        self.password_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=6)
        self.password_entry.insert(0, "admin123")

        # Remember me
        self.remember_var = tk.BooleanVar(value=True)
        rem_frame = tk.Frame(form, bg=BG_CARD)
        rem_frame.pack(fill="x", pady=(0, 16))
        tk.Checkbutton(rem_frame, text="Se souvenir de moi", variable=self.remember_var,
                      bg=BG_CARD, fg=TEXT_SECONDARY, activebackground=BG_CARD,
                      selectcolor=BG_CARD2, font=("Segoe UI", 9)).pack(side="left")

        self.error_label = tk.Label(form, text="", font=("Segoe UI", 9),
                                     bg=BG_CARD, fg=ACCENT_RED)
        self.error_label.pack()

        self.login_btn = ModernButton(form, "  Connexion  →", self._do_login,
                                      color=ACCENT_ORANGE, font_size=11)
        self.login_btn.pack(fill="x", pady=(0, 0), ipady=4)

        self.password_entry.bind("<Return>", lambda e: self._do_login())
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())

        # Version
        tk.Label(main, text="v1.0.0 • Le Schéma School ERP", font=("Segoe UI", 8),
                bg=BG_DARK, fg=TEXT_MUTED).pack(pady=(15, 0))

    def _animate_in(self):
        self.attributes("-alpha", 0)
        self._alpha = 0
        self._fade_in()

    def _fade_in(self):
        self._alpha += 0.05
        if self._alpha <= 1.0:
            self.attributes("-alpha", self._alpha)
            self.after(20, self._fade_in)

    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            self.error_label.config(text="Veuillez remplir tous les champs")
            return

        session = get_session()
        user = session.query(User).filter_by(
            username=username,
            password_hash=hash_password(password),
            is_active=True
        ).first()

        if user:
            user.last_login = datetime.now()
            session.commit()
            session.close()
            self.destroy()
            self.on_success({"username": username, "role": user.role, "full_name": user.full_name})
        else:
            session.close()
            self.error_label.config(text="❌ Identifiants incorrects")
            self.password_entry.delete(0, "end")


# ─── MAIN APPLICATION ─────────────────────────────────────────────────────────

class SchoolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("Le Schéma - Gestion Scolaire")
        self.geometry("1280x780")
        self.minsize(1024, 680)
        self.configure(bg=BG_DARK)
        
        # Set icon
        icon_path = os.path.join(APP_DIR, "assets", "school_logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.current_user = None
        self.current_page = None
        self.sidebar_buttons = {}
        
        self._show_login()

    def _show_login(self):
        login = LoginScreen(self, self._on_login_success)
        self.wait_window(login)

    def _on_login_success(self, user_data):
        self.current_user = user_data
        self.deiconify()
        self.state("zoomed")
        self._build_main_ui()
        self._navigate("dashboard")

    def _build_main_ui(self):
        # Clear existing widgets
        for w in self.winfo_children():
            w.destroy()

        # Main layout
        self.main_frame = tk.Frame(self, bg=BG_DARK)
        self.main_frame.pack(fill="both", expand=True)

        # Sidebar
        self._build_sidebar()

        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=BG_DARK)
        self.content_frame.pack(side="left", fill="both", expand=True)

        # Top navbar
        self._build_navbar()

        # Page content area
        self.page_frame = tk.Frame(self.content_frame, bg=BG_DARK, padx=20, pady=15)
        self.page_frame.pack(fill="both", expand=True)

    def _build_sidebar(self):
        sidebar = tk.Frame(self.main_frame, bg=BG_SIDEBAR, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo area
        logo_area = tk.Frame(sidebar, bg=BG_SIDEBAR, pady=20, padx=15)
        logo_area.pack(fill="x")

        logo_path = os.path.join(APP_DIR, "assets", "school_logo.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(logo_path).resize((50, 50), Image.LANCZOS)
            self._sidebar_logo = ImageTk.PhotoImage(img)
            tk.Label(logo_area, image=self._sidebar_logo, bg=BG_SIDEBAR).pack(side="left", padx=(0, 10))
        except Exception:
            tk.Label(logo_area, text="🎓", font=("Segoe UI Emoji", 24), bg=BG_SIDEBAR).pack(side="left", padx=(0,8))

        info = tk.Frame(logo_area, bg=BG_SIDEBAR)
        info.pack(side="left")
        tk.Label(info, text="Le Schéma", font=("Segoe UI", 11, "bold"),
                bg=BG_SIDEBAR, fg=ACCENT_ORANGE).pack(anchor="w")
        tk.Label(info, text="School ERP", font=("Segoe UI", 8),
                bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(anchor="w")

        # Divider
        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill="x", padx=15, pady=(0, 10))

        # Navigation items
        nav_items = [
            ("dashboard",   "Tableau de Bord",    "📊"),
            ("students",    "Élèves",              "👩‍🎓"),
            ("payments",    "Paiements",           "💳"),
            ("employees",   "Personnel",           "👨‍💼"),
            ("expenses",    "Dépenses",            "💸"),
            ("transport",   "Transport",           "🚌"),
            ("timetable",   "Emploi du Temps",     "📅"),
            ("documents",   "Documents",           "📁"),
            ("reports",     "Rapports",            "📈"),
            ("settings",    "Paramètres",          "⚙️"),
        ]

        role = self.current_user.get("role", "Admin")
        
        for page_id, label, icon in nav_items:
            # Role-based access
            if role == "Secrétaire" and page_id in ["expenses", "reports"]:
                continue
            if role == "Comptable" and page_id in ["timetable", "documents"]:
                continue

            btn = SidebarButton(sidebar, label, icon, lambda p=page_id: self._navigate(p))
            btn.pack(fill="x", padx=8, pady=1)
            self.sidebar_buttons[page_id] = btn

        # Spacer
        tk.Frame(sidebar, bg=BG_SIDEBAR).pack(fill="both", expand=True)

        # Bottom: user info & logout
        tk.Frame(sidebar, bg=BORDER_COLOR, height=1).pack(fill="x", padx=15)
        
        user_frame = tk.Frame(sidebar, bg=BG_SIDEBAR, padx=15, pady=12)
        user_frame.pack(fill="x")
        
        tk.Label(user_frame, text="👤", font=("Segoe UI Emoji", 14), bg=BG_SIDEBAR).pack(side="left")
        info2 = tk.Frame(user_frame, bg=BG_SIDEBAR)
        info2.pack(side="left", padx=8)
        tk.Label(info2, text=self.current_user.get("full_name", "Admin")[:16],
                font=("Segoe UI", 9, "bold"), bg=BG_SIDEBAR, fg=TEXT_PRIMARY).pack(anchor="w")
        tk.Label(info2, text=self.current_user.get("role", ""),
                font=("Segoe UI", 8), bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(anchor="w")

        logout_btn = tk.Label(user_frame, text="⏻", font=("Segoe UI Emoji", 14),
                             bg=BG_SIDEBAR, fg=ACCENT_RED, cursor="hand2")
        logout_btn.pack(side="right")
        logout_btn.bind("<Button-1>", self._logout)

    def _build_navbar(self):
        navbar = tk.Frame(self.content_frame, bg=BG_SIDEBAR, height=55)
        navbar.pack(fill="x")
        navbar.pack_propagate(False)

        # Page title
        self.nav_title = tk.Label(navbar, text="Tableau de Bord", font=("Segoe UI", 14, "bold"),
                                   bg=BG_SIDEBAR, fg=TEXT_PRIMARY)
        self.nav_title.pack(side="left", padx=20, pady=15)

        # Right section
        right = tk.Frame(navbar, bg=BG_SIDEBAR)
        right.pack(side="right", padx=20, pady=10)

        # Date/time
        self.clock_label = tk.Label(right, font=("Segoe UI", 9), bg=BG_SIDEBAR, fg=TEXT_SECONDARY)
        self.clock_label.pack(side="right", padx=10)
        self._update_clock()

        # School year
        settings = get_settings()
        year = settings.get("current_year", "2025-2026")
        tk.Label(right, text=f"🗓 {year}", font=("Segoe UI", 9),
                bg=BG_SIDEBAR, fg=ACCENT_ORANGE).pack(side="right", padx=10)

    def _update_clock(self):
        now = datetime.now().strftime("%d/%m/%Y  %H:%M")
        self.clock_label.config(text=f"🕐 {now}")
        self.after(30000, self._update_clock)

    def _navigate(self, page_id):
        # Update sidebar buttons
        for pid, btn in self.sidebar_buttons.items():
            btn.set_active(pid == page_id)

        # Update nav title
        titles = {
            "dashboard": "📊  Tableau de Bord",
            "students": "👩‍🎓  Gestion des Élèves",
            "payments": "💳  Gestion des Paiements",
            "employees": "👨‍💼  Gestion du Personnel",
            "expenses": "💸  Gestion des Dépenses",
            "transport": "🚌  Gestion du Transport",
            "timetable": "📅  Emploi du Temps",
            "documents": "📁  Gestion des Documents",
            "reports": "📈  Rapports & Exports",
            "settings": "⚙️  Paramètres",
        }
        self.nav_title.config(text=titles.get(page_id, page_id))
        self.current_page = page_id

        # Clear page frame
        for w in self.page_frame.winfo_children():
            w.destroy()

        # Load page
        pages = {
            "dashboard": DashboardPage,
            "students": StudentsPage,
            "payments": PaymentsPage,
            "employees": EmployeesPage,
            "expenses": ExpensesPage,
            "transport": TransportPage,
            "timetable": TimetablePage,
            "documents": DocumentsPage,
            "reports": ReportsPage,
            "settings": SettingsPage,
        }

        PageClass = pages.get(page_id)
        if PageClass:
            PageClass(self.page_frame, self.current_user, self).pack(fill="both", expand=True)

    def _logout(self, e=None):
        if messagebox.askyesno("Déconnexion", "Voulez-vous vraiment vous déconnecter ?"):
            self.current_user = None
            for w in self.winfo_children():
                w.destroy()
            self.geometry("1280x780")
            self.state("normal")
            self._show_login()

    def run(self):
        self.mainloop()


# ─── DASHBOARD PAGE ───────────────────────────────────────────────────────────

class DashboardPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        session = get_session()
        
        # Stats
        total_students = session.query(Student).filter_by(is_active=True).count()
        total_employees = session.query(Employee).filter_by(is_active=True).count()
        teachers = session.query(Employee).filter(Employee.role=="Enseignant", Employee.is_active==True).count()
        transport_students = session.query(Student).filter_by(transport=True, is_active=True).count()
        
        now = datetime.now()
        month_payments = session.query(Payment).filter(
            Payment.payment_date >= datetime(now.year, now.month, 1)
        ).all()
        monthly_rev = sum(p.amount for p in month_payments)
        
        year_payments = session.query(Payment).filter(
            Payment.payment_date >= datetime(now.year, 1, 1)
        ).all()
        yearly_rev = sum(p.amount for p in year_payments)
        
        year_expenses = session.query(Expense).filter(
            Expense.date >= date(now.year, 1, 1)
        ).all()
        total_expenses = sum(e.amount for e in year_expenses)
        profit = yearly_rev - total_expenses
        
        unpaid = session.query(Student).filter_by(is_active=True).count()  # simplified
        
        session.close()
        settings = get_settings()
        currency = settings.get("currency", "MAD")

        # Welcome
        greet = tk.Frame(self, bg=BG_DARK)
        greet.pack(fill="x", pady=(0, 15))
        
        now_str = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(greet, text=f"Bonjour, {self.user.get('full_name', 'Admin')} 👋",
                font=("Segoe UI", 18, "bold"), bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w")
        tk.Label(greet, text=now_str, font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")

        # Stats grid
        stats_frame = tk.Frame(self, bg=BG_DARK)
        stats_frame.pack(fill="x", pady=(0, 20))

        stats = [
            ("Élèves Actifs", total_students, "🎓", ACCENT_BLUE),
            (f"Revenu Mensuel ({currency})", f"{monthly_rev:,.0f}", "💰", ACCENT_GREEN),
            (f"Revenu Annuel ({currency})", f"{yearly_rev:,.0f}", "📈", ACCENT_ORANGE),
            (f"Dépenses ({currency})", f"{total_expenses:,.0f}", "💸", ACCENT_RED),
            (f"Bénéfice ({currency})", f"{profit:,.0f}", "💎", ACCENT_PURPLE),
            ("Transport", transport_students, "🚌", ACCENT_YELLOW),
            ("Enseignants", teachers, "👨‍🏫", ACCENT_BLUE),
            ("Personnel Total", total_employees, "👥", ACCENT_ORANGE),
        ]

        for i, (title, value, icon, color) in enumerate(stats):
            card = StatCard(stats_frame, title, value, icon, color)
            card.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")

        for col in range(4):
            stats_frame.grid_columnconfigure(col, weight=1)

        # Bottom section: notifications + quick actions
        bottom = tk.Frame(self, bg=BG_DARK)
        bottom.pack(fill="both", expand=True)

        # Notifications panel
        notif_frame = Card(bottom, padx=0, pady=0)
        notif_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(notif_frame, text="🔔  Notifications", font=("Segoe UI", 11, "bold"),
                bg=BG_CARD, fg=TEXT_PRIMARY, padx=15, pady=12).pack(anchor="w", fill="x")
        tk.Frame(notif_frame, bg=BORDER_COLOR, height=1).pack(fill="x")

        notifications = [
            (f"🎓  {total_students} élèves actifs inscrits", ACCENT_BLUE),
            (f"💰  Revenu mensuel: {monthly_rev:,.0f} {currency}", ACCENT_GREEN),
            (f"👥  {total_employees} membres du personnel actifs", ACCENT_ORANGE),
            (f"🚌  {transport_students} élèves abonnés au transport", ACCENT_PURPLE),
            ("⚠️  Vérifier les paiements en attente", ACCENT_YELLOW),
        ]
        
        for msg, color in notifications:
            notif_row = tk.Frame(notif_frame, bg=BG_CARD, padx=15, pady=8)
            notif_row.pack(fill="x")
            tk.Label(notif_row, text=msg, font=("Segoe UI", 9),
                    bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
            tk.Frame(notif_frame, bg=BORDER_COLOR, height=1).pack(fill="x", padx=15)

        # Quick actions
        actions_frame = Card(bottom, padx=0, pady=0)
        actions_frame.pack(side="left", fill="both", expand=True)

        tk.Label(actions_frame, text="⚡  Actions Rapides", font=("Segoe UI", 11, "bold"),
                bg=BG_CARD, fg=TEXT_PRIMARY, padx=15, pady=12).pack(anchor="w", fill="x")
        tk.Frame(actions_frame, bg=BORDER_COLOR, height=1).pack(fill="x")

        actions = [
            ("➕  Ajouter un élève", "students", ACCENT_BLUE),
            ("💳  Enregistrer un paiement", "payments", ACCENT_GREEN),
            ("👨‍💼  Ajouter du personnel", "employees", ACCENT_ORANGE),
            ("💸  Saisir une dépense", "expenses", ACCENT_RED),
            ("📈  Voir les rapports", "reports", ACCENT_PURPLE),
        ]

        actions_inner = tk.Frame(actions_frame, bg=BG_CARD, padx=15, pady=15)
        actions_inner.pack(fill="both", expand=True)

        for label, page, color in actions:
            btn = ModernButton(actions_inner, label, lambda p=page: self.app._navigate(p),
                              color=BG_CARD2, fg=TEXT_PRIMARY, font_size=9)
            btn.config(anchor="w", padx=15, pady=6)
            btn.pack(fill="x", pady=3)


# ─── STUDENTS PAGE ────────────────────────────────────────────────────────────

class StudentsPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        ModernButton(toolbar, "➕  Ajouter Élève", self._add_student, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(toolbar, "✏️  Modifier", self._edit_student, color=ACCENT_BLUE).pack(side="left", padx=5)
        ModernButton(toolbar, "🗑  Supprimer", self._delete_student, color=ACCENT_RED).pack(side="left")

        # Search
        search_frame = tk.Frame(toolbar, bg=BG_CARD2, padx=10, pady=4)
        search_frame.pack(side="right")
        tk.Label(search_frame, text="🔍", bg=BG_CARD2, font=("Segoe UI Emoji", 11)).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._load_students())
        tk.Entry(search_frame, textvariable=self.search_var, bg=BG_CARD2, fg=TEXT_PRIMARY,
                insertbackground=TEXT_PRIMARY, relief="flat", font=("Segoe UI", 10),
                width=25).pack(side="left", padx=6, ipady=3)

        # Stats bar
        stats_bar = tk.Frame(self, bg=BG_DARK)
        stats_bar.pack(fill="x", pady=(0, 10))
        
        session = get_session()
        total = session.query(Student).filter_by(is_active=True).count()
        transport = session.query(Student).filter_by(transport=True, is_active=True).count()
        insured = session.query(Student).filter_by(insurance_paid=True, is_active=True).count()
        session.close()

        for label, val, color in [
            (f"Total: {total}", "🎓", ACCENT_BLUE),
            (f"Transport: {transport}", "🚌", ACCENT_ORANGE),
            (f"Assurés: {insured}", "🛡", ACCENT_GREEN),
        ]:
            chip = tk.Frame(stats_bar, bg=BG_CARD, padx=12, pady=5)
            chip.pack(side="left", padx=(0, 8))
            tk.Label(chip, text=f"{val}  {label}", font=("Segoe UI", 9, "bold"),
                    bg=BG_CARD, fg=color).pack()

        # Table
        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("code", "nom", "prenom", "classe", "parent", "phone", "transport", "assurance", "mensualite")
        heads = ("Code", "Nom", "Prénom", "Classe", "Parent", "Téléphone", "Transport", "Assurance", "Mensualité")
        
        self.tree = StyledTreeview(table_frame, cols, heads)

        widths = [90, 100, 100, 70, 130, 110, 70, 80, 90]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._view_student())

        self._load_students()

    def _load_students(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        query = session.query(Student).filter_by(is_active=True)
        
        search = self.search_var.get().strip().lower()
        if search:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Student.first_name.ilike(f"%{search}%"),
                    Student.last_name.ilike(f"%{search}%"),
                    Student.student_code.ilike(f"%{search}%"),
                    Student.class_name.ilike(f"%{search}%"),
                    Student.parent_name.ilike(f"%{search}%"),
                )
            )
        
        students = query.order_by(Student.last_name).all()
        for i, s in enumerate(students):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=s.id, tags=(tag,), values=(
                s.student_code, s.last_name, s.first_name, s.class_name or "",
                s.parent_name or "", s.parent_phone or "",
                "✅" if s.transport else "❌",
                "✅" if s.insurance_paid else "❌",
                f"{s.monthly_fee:.0f} MAD"
            ))
        session.close()

    def _add_student(self):
        StudentDialog(self, None, self._load_students)

    def _edit_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un élève")
            return
        student_id = int(sel[0])
        StudentDialog(self, student_id, self._load_students)

    def _delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un élève")
            return
        if messagebox.askyesno("Confirmer", "Voulez-vous vraiment supprimer cet élève ?"):
            session = get_session()
            s = session.query(Student).get(int(sel[0]))
            if s:
                s.is_active = False
                session.commit()
            session.close()
            self._load_students()

    def _view_student(self):
        sel = self.tree.selection()
        if sel:
            StudentDialog(self, int(sel[0]), self._load_students)


class StudentDialog(tk.Toplevel):
    def __init__(self, parent, student_id, on_save):
        super().__init__(parent)
        self.student_id = student_id
        self.on_save = on_save
        self.title("Ajouter Élève" if not student_id else "Modifier Élève")
        self.geometry("680x720")
        self.configure(bg=BG_DARK)
        self.grab_set()
        
        x = (self.winfo_screenwidth() - 680) // 2
        y = (self.winfo_screenheight() - 720) // 2
        self.geometry(f"680x720+{x}+{y}")

        self.student = None
        if student_id:
            session = get_session()
            self.student = session.query(Student).get(student_id)
            session.close()

        self._build()

    def _build(self):
        # Header
        header = tk.Frame(self, bg=ACCENT_ORANGE, padx=20, pady=12)
        header.pack(fill="x")
        title = "Ajouter un Élève" if not self.student_id else "Modifier l'Élève"
        tk.Label(header, text=f"🎓  {title}", font=("Segoe UI", 13, "bold"),
                bg=ACCENT_ORANGE, fg=TEXT_PRIMARY).pack(anchor="w")

        # Scrollable form
        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        form = tk.Frame(canvas, bg=BG_DARK, padx=25, pady=20)
        canvas_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        form.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_configure)

        self.fields = {}

        def add_row(parent, label, widget_type="entry", options=None, row=None, column=0):
            pass

        def labeled_entry(label, var_name, value="", row_frame=None):
            if row_frame:
                parent = row_frame
            else:
                parent = form

            lbl = tk.Label(parent, text=label, font=("Segoe UI", 9),
                          bg=BG_DARK, fg=TEXT_SECONDARY, anchor="w")
            lbl.pack(anchor="w")

            ent_frame = tk.Frame(parent, bg=BG_CARD2, padx=10, pady=3)
            ent_frame.pack(fill="x", pady=(2, 12))
            ent = tk.Entry(ent_frame, bg=BG_CARD2, fg=TEXT_PRIMARY,
                          insertbackground=TEXT_PRIMARY, relief="flat",
                          font=("Segoe UI", 10), bd=0)
            ent.pack(fill="x", ipady=5)
            if value:
                ent.insert(0, value)
            self.fields[var_name] = ent
            return ent

        def labeled_combo(label, var_name, values, value=""):
            lbl = tk.Label(form, text=label, font=("Segoe UI", 9),
                          bg=BG_DARK, fg=TEXT_SECONDARY, anchor="w")
            lbl.pack(anchor="w")

            style = ttk.Style()
            style.configure("Dark.TCombobox",
                fieldbackground=BG_CARD2, background=BG_CARD2,
                foreground=TEXT_PRIMARY, selectbackground=ACCENT_ORANGE)

            var = tk.StringVar(value=value)
            combo = ttk.Combobox(form, textvariable=var, values=values,
                                state="readonly", font=("Segoe UI", 10))
            combo.pack(fill="x", pady=(2, 12), ipady=4)
            self.fields[var_name] = var
            return combo

        s = self.student

        # Two-column rows
        row1 = tk.Frame(form, bg=BG_DARK)
        row1.pack(fill="x")
        row1.grid_columnconfigure(0, weight=1)
        row1.grid_columnconfigure(1, weight=1)

        # We'll do simple stacked layout for clarity
        labeled_entry("Nom *", "last_name", s.last_name if s else "")
        labeled_entry("Prénom *", "first_name", s.first_name if s else "")
        labeled_combo("Classe *", "class_name", CLASSES, s.class_name if s else "")
        
        tk.Label(form, text="Genre", font=("Segoe UI", 9),
                bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
        gender_var = tk.StringVar(value=(s.gender if s else "Masculin"))
        gender_frame = tk.Frame(form, bg=BG_DARK)
        gender_frame.pack(anchor="w", pady=(0, 12))
        tk.Radiobutton(gender_frame, text="Masculin", variable=gender_var, value="Masculin",
                      bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_CARD2,
                      activebackground=BG_DARK, font=("Segoe UI", 9)).pack(side="left")
        tk.Radiobutton(gender_frame, text="Féminin", variable=gender_var, value="Féminin",
                      bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_CARD2,
                      activebackground=BG_DARK, font=("Segoe UI", 9)).pack(side="left", padx=20)
        self.fields["gender"] = gender_var

        labeled_entry("Date de Naissance (JJ/MM/AAAA)", "birth_date",
                     s.birth_date.strftime("%d/%m/%Y") if (s and s.birth_date) else "")
        labeled_entry("Adresse", "address", s.address if s else "")
        labeled_entry("Nom du Parent/Tuteur", "parent_name", s.parent_name if s else "")
        labeled_entry("Téléphone Parent", "parent_phone", s.parent_phone if s else "")
        labeled_entry("Téléphone Urgence", "emergency_phone", s.emergency_phone if s else "")
        labeled_entry("Frais Mensuel (MAD)", "monthly_fee", str(s.monthly_fee) if s else "0")

        # Boolean fields
        self.transport_var = tk.BooleanVar(value=(s.transport if s else False))
        self.insurance_var = tk.BooleanVar(value=(s.insurance_paid if s else False))

        check_frame = tk.Frame(form, bg=BG_DARK)
        check_frame.pack(anchor="w", pady=(0, 12))
        tk.Checkbutton(check_frame, text="✅ Abonné Transport", variable=self.transport_var,
                      bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_CARD2,
                      activebackground=BG_DARK, font=("Segoe UI", 9)).pack(side="left")
        tk.Checkbutton(check_frame, text="🛡 Assurance Payée", variable=self.insurance_var,
                      bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=BG_CARD2,
                      activebackground=BG_DARK, font=("Segoe UI", 9)).pack(side="left", padx=30)

        labeled_entry("Notes", "notes", s.notes if s else "")

        # Buttons
        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(10, 0))
        ModernButton(btn_frame, "💾  Enregistrer", self._save, color=ACCENT_ORANGE).pack(side="left", padx=(0, 10))
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left")

    def _save(self):
        last_name = self.fields["last_name"].get().strip()
        first_name = self.fields["first_name"].get().strip()
        class_name = self.fields["class_name"].get()

        if not last_name or not first_name or not class_name:
            messagebox.showerror("Erreur", "Nom, Prénom et Classe sont obligatoires")
            return

        try:
            monthly_fee = float(self.fields["monthly_fee"].get() or 0)
        except ValueError:
            monthly_fee = 0.0

        birth_date = None
        bd_str = self.fields["birth_date"].get().strip()
        if bd_str:
            try:
                birth_date = datetime.strptime(bd_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        session = get_session()
        if self.student_id:
            s = session.query(Student).get(self.student_id)
        else:
            s = Student(student_code=next_student_code())
            session.add(s)

        s.last_name = last_name
        s.first_name = first_name
        s.class_name = class_name
        s.gender = self.fields["gender"].get()
        s.birth_date = birth_date
        s.address = self.fields["address"].get().strip()
        s.parent_name = self.fields["parent_name"].get().strip()
        s.parent_phone = self.fields["parent_phone"].get().strip()
        s.emergency_phone = self.fields["emergency_phone"].get().strip()
        s.monthly_fee = monthly_fee
        s.transport = self.transport_var.get()
        s.insurance_paid = self.insurance_var.get()
        s.notes = self.fields["notes"].get().strip()

        session.commit()
        session.close()

        messagebox.showinfo("Succès", "Élève enregistré avec succès !")
        self.on_save()
        self.destroy()


# ─── PAYMENTS PAGE ────────────────────────────────────────────────────────────

class PaymentsPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        ModernButton(toolbar, "➕  Nouveau Paiement", self._add_payment, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(toolbar, "🖨  Imprimer Reçu", self._print_receipt, color=ACCENT_BLUE).pack(side="left", padx=5)

        # Filter by type
        filter_frame = tk.Frame(toolbar, bg=BG_DARK)
        filter_frame.pack(side="right")

        self.filter_var = tk.StringVar(value="Tous")
        for label in ["Tous", "Mensuel", "Assurance", "Transport"]:
            tk.Radiobutton(filter_frame, text=label, variable=self.filter_var, value=label,
                          bg=BG_DARK, fg=TEXT_SECONDARY, selectcolor=ACCENT_ORANGE,
                          activebackground=BG_DARK, font=("Segoe UI", 9),
                          command=self._load_payments).pack(side="left", padx=5)

        # Table
        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("receipt", "date", "student", "class_", "type", "month", "amount", "by")
        heads = ("N° Reçu", "Date", "Élève", "Classe", "Type", "Mois", "Montant", "Par")

        self.tree = StyledTreeview(table_frame, cols, heads)
        widths = [120, 130, 150, 70, 100, 80, 100, 100]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._load_payments()

    def _load_payments(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        payments = session.query(Payment).order_by(Payment.payment_date.desc()).limit(200).all()

        f = self.filter_var.get()
        type_map = {"Mensuel": "monthly", "Assurance": "insurance", "Transport": "transport"}

        settings = get_settings()
        currency = settings.get("currency", "MAD")

        for i, p in enumerate(payments):
            if f != "Tous" and p.payment_type != type_map.get(f):
                continue
            student = p.student
            name = f"{student.last_name} {student.first_name}" if student else ""
            class_ = student.class_name if student else ""
            tag = "even" if i % 2 == 0 else "odd"
            type_labels = {"monthly": "Mensuel", "insurance": "Assurance", "transport": "Transport"}
            self.tree.insert("", "end", iid=p.id, tags=(tag,), values=(
                p.receipt_number or "",
                p.payment_date.strftime("%d/%m/%Y %H:%M") if p.payment_date else "",
                name, class_,
                type_labels.get(p.payment_type, p.payment_type or ""),
                p.month or "",
                f"{p.amount:,.2f} {currency}",
                p.created_by or ""
            ))
        session.close()

    def _add_payment(self):
        PaymentDialog(self, self.user, self._load_payments)

    def _print_receipt(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un paiement")
            return
        payment_id = int(sel[0])
        session = get_session()
        p = session.query(Payment).get(payment_id)
        if p and p.receipt_path and os.path.exists(p.receipt_path):
            import subprocess
            try:
                if sys.platform == "win32":
                    os.startfile(p.receipt_path, "print")
                elif sys.platform == "darwin":
                    subprocess.call(["lpr", p.receipt_path])
                else:
                    subprocess.call(["lpr", p.receipt_path])
            except Exception as e:
                messagebox.showinfo("Reçu", f"Reçu: {p.receipt_path}")
        else:
            messagebox.showwarning("Reçu", "Reçu non disponible")
        session.close()


class PaymentDialog(tk.Toplevel):
    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.user = user
        self.on_save = on_save
        self.title("Nouveau Paiement")
        self.geometry("550x600")
        self.configure(bg=BG_DARK)
        self.grab_set()
        
        x = (self.winfo_screenwidth() - 550) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"550x600+{x}+{y}")

        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_GREEN, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="💳  Enregistrer un Paiement", font=("Segoe UI", 13, "bold"),
                bg=ACCENT_GREEN, fg=TEXT_PRIMARY).pack(anchor="w")

        form = tk.Frame(self, bg=BG_DARK, padx=25, pady=20)
        form.pack(fill="both", expand=True)

        def lbl(text):
            tk.Label(form, text=text, font=("Segoe UI", 9),
                    bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")

        def entry_widget(default=""):
            ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 12))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0)
            e.pack(fill="x", ipady=5)
            if default:
                e.insert(0, default)
            return e

        # Student search
        lbl("Rechercher Élève (Nom ou Code)")
        search_ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
        search_ef.pack(fill="x", pady=(2, 4))
        self.student_search = tk.Entry(search_ef, bg=BG_CARD2, fg=TEXT_PRIMARY,
                                        insertbackground=TEXT_PRIMARY, relief="flat",
                                        font=("Segoe UI", 10), bd=0)
        self.student_search.pack(fill="x", ipady=5)

        self.student_listbox = tk.Listbox(form, bg=BG_CARD2, fg=TEXT_PRIMARY,
                                          selectbackground=ACCENT_ORANGE,
                                          font=("Segoe UI", 9), height=5, relief="flat")
        self.student_listbox.pack(fill="x", pady=(0, 12))

        self.selected_student = None
        self.student_label = tk.Label(form, text="Aucun élève sélectionné",
                                       font=("Segoe UI", 9, "italic"),
                                       bg=BG_DARK, fg=TEXT_MUTED)
        self.student_label.pack(anchor="w", pady=(0, 10))

        self.student_search.bind("<KeyRelease>", self._search_students)
        self.student_listbox.bind("<<ListboxSelect>>", self._select_student)

        # Payment type
        lbl("Type de Paiement")
        self.ptype_var = tk.StringVar(value="monthly")
        type_frame = tk.Frame(form, bg=BG_DARK)
        type_frame.pack(anchor="w", pady=(0, 12))
        for label, val in [("Mensuel", "monthly"), ("Assurance", "insurance"), ("Transport", "transport")]:
            tk.Radiobutton(type_frame, text=label, variable=self.ptype_var, value=val,
                          bg=BG_DARK, fg=TEXT_PRIMARY, selectcolor=ACCENT_ORANGE,
                          activebackground=BG_DARK, font=("Segoe UI", 9),
                          command=self._on_type_change).pack(side="left", padx=5)

        lbl("Mois")
        self.month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        month_combo = ttk.Combobox(form, textvariable=self.month_var, state="readonly",
                                   values=["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                                           "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
                                   font=("Segoe UI", 10))
        month_combo.pack(fill="x", pady=(2, 12), ipady=4)

        lbl("Montant (MAD)")
        self.amount_entry = entry_widget("0")

        lbl("Notes (optionnel)")
        self.notes_entry = entry_widget()

        # Buttons
        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(10, 0))
        ModernButton(btn_frame, "💾  Enregistrer & Générer Reçu", self._save, color=ACCENT_GREEN).pack(side="left")
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left", padx=10)

        self._students = []
        self._load_all_students()

    def _load_all_students(self):
        session = get_session()
        self._students = session.query(Student).filter_by(is_active=True).all()
        self._students_data = [(s.id, f"{s.last_name} {s.first_name}", s.student_code, 
                                s.class_name, s.monthly_fee, s.parent_name) for s in self._students]
        session.close()

    def _search_students(self, e=None):
        search = self.student_search.get().strip().lower()
        self.student_listbox.delete(0, "end")
        for sid, name, code, cls, fee, parent in self._students_data:
            if search in name.lower() or search in code.lower():
                self.student_listbox.insert("end", f"{code} - {name} ({cls})")
        self._filtered = [(sid, name, code, cls, fee, parent) 
                          for sid, name, code, cls, fee, parent in self._students_data
                          if search in name.lower() or search in code.lower()]

    def _select_student(self, e=None):
        sel = self.student_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if hasattr(self, "_filtered") and idx < len(self._filtered):
            data = self._filtered[idx]
        else:
            data = self._students_data[idx]
        self.selected_student = data
        self.student_label.config(
            text=f"✅ Sélectionné: {data[1]} | Classe: {data[3]} | Frais: {data[4]:.0f} MAD",
            fg=ACCENT_GREEN
        )
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, str(data[4]))
        self._on_type_change()

    def _on_type_change(self):
        if not self.selected_student:
            return
        settings = get_settings()
        ptype = self.ptype_var.get()
        if ptype == "monthly":
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, str(self.selected_student[4]))
        elif ptype == "insurance":
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, settings.get("insurance_fee", "500"))
        elif ptype == "transport":
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, settings.get("transport_fee", "300"))

    def _save(self):
        if not self.selected_student:
            messagebox.showerror("Erreur", "Veuillez sélectionner un élève")
            return

        try:
            amount = float(self.amount_entry.get() or 0)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide")
            return

        receipt_num = next_receipt_number()
        settings = get_settings()

        session = get_session()
        student = session.query(Student).get(self.selected_student[0])

        payment = Payment(
            receipt_number=receipt_num,
            student_id=student.id,
            payment_type=self.ptype_var.get(),
            amount=amount,
            payment_date=datetime.now(),
            month=self.month_var.get(),
            year=datetime.now().year,
            notes=self.notes_entry.get().strip(),
            created_by=self.user.get("username", "admin")
        )

        # Generate receipt
        receipts_dir = os.path.join(APP_DIR, "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        receipt_path = os.path.join(receipts_dir, f"{receipt_num}.pdf")

        student_data = {
            "first_name": student.first_name,
            "last_name": student.last_name,
            "student_code": student.student_code,
            "class_name": student.class_name or "",
            "parent_name": student.parent_name or "",
        }
        payment_data = {
            "receipt_number": receipt_num,
            "payment_type": self.ptype_var.get(),
            "amount": amount,
            "payment_date": datetime.now(),
            "month": self.month_var.get(),
            "year": datetime.now().year,
            "notes": self.notes_entry.get().strip(),
        }

        try:
            generate_receipt(payment_data, student_data, settings, receipt_path)
            payment.receipt_path = receipt_path
        except Exception as ex:
            print(f"Receipt error: {ex}")

        # Update student insurance if applicable
        if self.ptype_var.get() == "insurance":
            student.insurance_paid = True

        session.add(payment)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", f"✅ Paiement enregistré!\nReçu: {receipt_num}")
        
        # Open receipt
        if os.path.exists(receipt_path):
            try:
                if sys.platform == "win32":
                    os.startfile(receipt_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", receipt_path])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", receipt_path])
            except Exception:
                pass

        self.on_save()
        self.destroy()


# ─── EMPLOYEES PAGE ───────────────────────────────────────────────────────────

class EmployeesPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        ModernButton(toolbar, "➕  Ajouter Personnel", self._add, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(toolbar, "✏️  Modifier", self._edit, color=ACCENT_BLUE).pack(side="left", padx=5)
        ModernButton(toolbar, "💰  Gérer Salaires", self._manage_salary, color=ACCENT_GREEN).pack(side="left")

        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("code", "nom", "prenom", "role", "phone", "salaire", "embauche", "statut")
        heads = ("Code", "Nom", "Prénom", "Poste", "Téléphone", "Salaire Base", "Date Embauche", "Statut")

        self.tree = StyledTreeview(table_frame, cols, heads)
        widths = [90, 100, 100, 120, 110, 100, 110, 70]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        employees = session.query(Employee).filter_by(is_active=True).order_by(Employee.last_name).all()
        for i, e in enumerate(employees):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=e.id, tags=(tag,), values=(
                e.employee_code or "",
                e.last_name, e.first_name,
                e.role or "",
                e.phone or "",
                f"{e.base_salary:,.0f} MAD",
                e.hire_date.strftime("%d/%m/%Y") if e.hire_date else "",
                "✅ Actif"
            ))
        session.close()

    def _add(self):
        EmployeeDialog(self, None, self._load)

    def _edit(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un employé")
            return
        EmployeeDialog(self, int(sel[0]), self._load)

    def _manage_salary(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un employé")
            return
        SalaryDialog(self, int(sel[0]))


class EmployeeDialog(tk.Toplevel):
    def __init__(self, parent, emp_id, on_save):
        super().__init__(parent)
        self.emp_id = emp_id
        self.on_save = on_save
        self.title("Ajouter Personnel" if not emp_id else "Modifier Personnel")
        self.geometry("600x600")
        self.configure(bg=BG_DARK)
        self.grab_set()

        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 600) // 2
        self.geometry(f"600x600+{x}+{y}")

        self.emp = None
        if emp_id:
            session = get_session()
            self.emp = session.query(Employee).get(emp_id)
            session.close()

        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_BLUE, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="👨‍💼  Gestion du Personnel", font=("Segoe UI", 13, "bold"),
                bg=ACCENT_BLUE, fg=TEXT_PRIMARY).pack(anchor="w")

        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        form = tk.Frame(canvas, bg=BG_DARK, padx=25, pady=20)
        cw = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=canvas.winfo_width()))

        self.fields = {}
        e = self.emp

        def labeled_entry(label, key, value=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 12))
            ent = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                          relief="flat", font=("Segoe UI", 10), bd=0)
            ent.pack(fill="x", ipady=5)
            if value:
                ent.insert(0, str(value))
            self.fields[key] = ent

        def labeled_combo(label, key, values, value=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            var = tk.StringVar(value=value)
            combo = ttk.Combobox(form, textvariable=var, values=values, state="readonly", font=("Segoe UI", 10))
            combo.pack(fill="x", pady=(2, 12), ipady=4)
            self.fields[key] = var

        labeled_entry("Nom *", "last_name", e.last_name if e else "")
        labeled_entry("Prénom *", "first_name", e.first_name if e else "")
        labeled_combo("Poste *", "role",
                     ["Enseignant", "Directeur", "Secrétaire", "Comptable", "Chauffeur", "Agent d'entretien", "Autre"],
                     e.role if e else "")
        labeled_entry("Matière (si enseignant)", "subject", e.subject if e else "")
        labeled_entry("Téléphone", "phone", e.phone if e else "")
        labeled_entry("Email", "email", e.email if e else "")
        labeled_entry("CIN", "cin", e.cin if e else "")
        labeled_entry("Salaire de Base (MAD)", "base_salary", str(e.base_salary) if e else "0")
        labeled_entry("Date d'Embauche (JJ/MM/AAAA)", "hire_date",
                     e.hire_date.strftime("%d/%m/%Y") if (e and e.hire_date) else "")

        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(10, 0))
        ModernButton(btn_frame, "💾  Enregistrer", self._save, color=ACCENT_BLUE).pack(side="left", padx=(0, 10))
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left")

    def _save(self):
        last = self.fields["last_name"].get().strip()
        first = self.fields["first_name"].get().strip()
        role = self.fields["role"].get()

        if not last or not first:
            messagebox.showerror("Erreur", "Nom et Prénom sont obligatoires")
            return

        try:
            salary = float(self.fields["base_salary"].get() or 0)
        except ValueError:
            salary = 0.0

        hire_date = None
        hd_str = self.fields["hire_date"].get().strip()
        if hd_str:
            try:
                hire_date = datetime.strptime(hd_str, "%d/%m/%Y").date()
            except ValueError:
                pass

        session = get_session()
        if self.emp_id:
            emp = session.query(Employee).get(self.emp_id)
        else:
            emp = Employee(employee_code=next_employee_code())
            session.add(emp)

        emp.last_name = last
        emp.first_name = first
        emp.role = role
        emp.subject = self.fields["subject"].get().strip()
        emp.phone = self.fields["phone"].get().strip()
        emp.email = self.fields["email"].get().strip()
        emp.cin = self.fields["cin"].get().strip()
        emp.base_salary = salary
        emp.hire_date = hire_date

        session.commit()
        session.close()

        messagebox.showinfo("Succès", "Personnel enregistré avec succès!")
        self.on_save()
        self.destroy()


class SalaryDialog(tk.Toplevel):
    def __init__(self, parent, emp_id):
        super().__init__(parent)
        self.emp_id = emp_id
        self.title("Gestion des Salaires")
        self.geometry("600x500")
        self.configure(bg=BG_DARK)
        self.grab_set()

        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"600x500+{x}+{y}")

        session = get_session()
        self.emp = session.query(Employee).get(emp_id)
        session.close()

        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_GREEN, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text=f"💰  Salaires - {self.emp.last_name} {self.emp.first_name}",
                font=("Segoe UI", 13, "bold"), bg=ACCENT_GREEN, fg=TEXT_PRIMARY).pack(anchor="w")

        # Add salary form
        form = tk.Frame(self, bg=BG_DARK, padx=20, pady=15)
        form.pack(fill="x")

        row = tk.Frame(form, bg=BG_DARK)
        row.pack(fill="x")

        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

        def make_entry(parent, label, default=""):
            tk.Label(parent, text=label, font=("Segoe UI", 8), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(parent, bg=BG_CARD2, padx=8, pady=2)
            ef.pack(fill="x", pady=(1, 8))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 9), bd=0)
            e.pack(fill="x", ipady=4)
            if default:
                e.insert(0, str(default))
            return e

        left = tk.Frame(form, bg=BG_DARK)
        left.pack(side="left", fill="x", expand=True, padx=(0, 10))
        right = tk.Frame(form, bg=BG_DARK)
        right.pack(side="left", fill="x", expand=True)

        tk.Label(left, text="Mois", font=("Segoe UI", 8), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
        self.month_var = tk.StringVar(value=datetime.now().strftime("%B"))
        month_combo = ttk.Combobox(left, textvariable=self.month_var, values=months,
                                   state="readonly", font=("Segoe UI", 9))
        month_combo.pack(fill="x", pady=(1, 8), ipady=3)

        self.base_ent = make_entry(left, "Salaire de Base (MAD)", str(self.emp.base_salary))
        self.bonus_ent = make_entry(right, "Bonus (MAD)", "0")
        self.deduct_ent = make_entry(right, "Déductions (MAD)", "0")

        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(5, 0))
        ModernButton(btn_frame, "💾  Enregistrer Salaire", self._save_salary, color=ACCENT_GREEN).pack(side="left")

        # History
        tk.Label(self, text="Historique des Salaires", font=("Segoe UI", 10, "bold"),
                bg=BG_DARK, fg=TEXT_PRIMARY, padx=20, pady=5).pack(anchor="w")

        hist_frame = Card(self, padx=0, pady=0)
        hist_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        cols = ("month", "year", "base", "bonus", "deduct", "net", "paid")
        heads = ("Mois", "Année", "Base", "Bonus", "Déduction", "Net", "Payé")

        self.hist_tree = StyledTreeview(hist_frame, cols, heads)
        for col in cols:
            self.hist_tree.column(col, width=70)
        self.hist_tree.pack(fill="both", expand=True)

        self._load_history()

    def _load_history(self):
        self.hist_tree.delete(*self.hist_tree.get_children())
        session = get_session()
        salaries = session.query(Salary).filter_by(employee_id=self.emp_id)\
                          .order_by(Salary.year.desc(), Salary.id.desc()).all()
        for s in salaries:
            self.hist_tree.insert("", "end", values=(
                s.month or "", s.year or "",
                f"{s.base_amount:,.0f}", f"{s.bonus:,.0f}", f"{s.deductions:,.0f}",
                f"{s.net_amount:,.0f} MAD",
                "✅" if s.paid else "❌"
            ))
        session.close()

    def _save_salary(self):
        try:
            base = float(self.base_ent.get() or 0)
            bonus = float(self.bonus_ent.get() or 0)
            deduct = float(self.deduct_ent.get() or 0)
        except ValueError:
            messagebox.showerror("Erreur", "Valeurs numériques invalides")
            return

        net = base + bonus - deduct
        session = get_session()
        sal = Salary(
            employee_id=self.emp_id,
            month=self.month_var.get(),
            year=datetime.now().year,
            base_amount=base,
            bonus=bonus,
            deductions=deduct,
            net_amount=net,
            paid=True,
            paid_date=datetime.now()
        )
        session.add(sal)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", f"Salaire enregistré: {net:,.0f} MAD")
        self._load_history()


# ─── EXPENSES PAGE ────────────────────────────────────────────────────────────

class ExpensesPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        ModernButton(toolbar, "➕  Ajouter Dépense", self._add, color=ACCENT_RED).pack(side="left")
        ModernButton(toolbar, "🗑  Supprimer", self._delete, color=BG_CARD2).pack(side="left", padx=5)

        # Total display
        self.total_label = tk.Label(toolbar, text="", font=("Segoe UI", 11, "bold"),
                                     bg=BG_DARK, fg=ACCENT_RED)
        self.total_label.pack(side="right")

        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("date", "category", "description", "type", "amount")
        heads = ("Date", "Catégorie", "Description", "Type", "Montant")

        self.tree = StyledTreeview(table_frame, cols, heads)
        widths = [100, 120, 200, 100, 120]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        expenses = session.query(Expense).order_by(Expense.date.desc()).limit(200).all()
        total = 0
        for i, exp in enumerate(expenses):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=exp.id, tags=(tag,), values=(
                exp.date.strftime("%d/%m/%Y") if exp.date else "",
                exp.category or "",
                exp.description or "",
                "Fixe" if exp.expense_type == "fixed" else "Variable",
                f"{exp.amount:,.2f} MAD"
            ))
            total += exp.amount
        session.close()
        self.total_label.config(text=f"Total: {total:,.2f} MAD")

    def _add(self):
        ExpenseDialog(self, self.user, self._load)

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez une dépense")
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette dépense ?"):
            session = get_session()
            exp = session.query(Expense).get(int(sel[0]))
            if exp:
                session.delete(exp)
                session.commit()
            session.close()
            self._load()


class ExpenseDialog(tk.Toplevel):
    def __init__(self, parent, user, on_save):
        super().__init__(parent)
        self.user = user
        self.on_save = on_save
        self.title("Ajouter une Dépense")
        self.geometry("480x460")
        self.configure(bg=BG_DARK)
        self.grab_set()

        x = (self.winfo_screenwidth() - 480) // 2
        y = (self.winfo_screenheight() - 460) // 2
        self.geometry(f"480x460+{x}+{y}")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_RED, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="💸  Nouvelle Dépense", font=("Segoe UI", 13, "bold"),
                bg=ACCENT_RED, fg=TEXT_PRIMARY).pack(anchor="w")

        form = tk.Frame(self, bg=BG_DARK, padx=25, pady=20)
        form.pack(fill="both", expand=True)

        def labeled_entry(label, default=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 12))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0)
            e.pack(fill="x", ipady=5)
            if default:
                e.insert(0, str(default))
            return e

        def labeled_combo(label, values, default=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            var = tk.StringVar(value=default)
            combo = ttk.Combobox(form, textvariable=var, values=values, state="readonly", font=("Segoe UI", 10))
            combo.pack(fill="x", pady=(2, 12), ipady=4)
            return var

        self.category_var = labeled_combo("Catégorie", 
            ["Salaires", "Fournitures", "Électricité", "Eau", "Loyer", "Transport", 
             "Maintenance", "Communication", "Autre"],
            "Fournitures")

        self.desc_entry = labeled_entry("Description")
        self.amount_entry = labeled_entry("Montant (MAD)", "0")

        self.type_var = labeled_combo("Type", ["Fixe", "Variable"], "Variable")

        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(10, 0))
        ModernButton(btn_frame, "💾  Enregistrer", self._save, color=ACCENT_RED).pack(side="left")
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left", padx=10)

    def _save(self):
        try:
            amount = float(self.amount_entry.get() or 0)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide")
            return

        session = get_session()
        exp = Expense(
            category=self.category_var.get(),
            description=self.desc_entry.get().strip(),
            amount=amount,
            expense_type="fixed" if self.type_var.get() == "Fixe" else "variable",
            date=date.today(),
            created_by=self.user.get("username", "admin")
        )
        session.add(exp)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", "Dépense enregistrée!")
        self.on_save()
        self.destroy()


# ─── TRANSPORT PAGE ───────────────────────────────────────────────────────────

class TransportPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        # Stats
        session = get_session()
        transport_count = session.query(Student).filter_by(transport=True, is_active=True).count()
        session.close()

        stats = tk.Frame(self, bg=BG_DARK)
        stats.pack(fill="x", pady=(0, 20))

        StatCard(stats, "Élèves avec Transport", transport_count, "🚌", ACCENT_BLUE).pack(side="left", padx=(0,10))

        # Students with transport
        tk.Label(self, text="Élèves Abonnés au Transport", font=("Segoe UI", 12, "bold"),
                bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 10))

        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("code", "nom", "prenom", "classe", "parent", "phone")
        heads = ("Code", "Nom", "Prénom", "Classe", "Parent", "Téléphone")

        tree = StyledTreeview(table_frame, cols, heads)
        for col in cols:
            tree.column(col, width=120)

        session = get_session()
        students = session.query(Student).filter_by(transport=True, is_active=True).all()
        for i, s in enumerate(students):
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", tags=(tag,), values=(
                s.student_code, s.last_name, s.first_name,
                s.class_name or "", s.parent_name or "", s.parent_phone or ""
            ))
        session.close()

        tree.pack(fill="both", expand=True)


# ─── TIMETABLE PAGE ───────────────────────────────────────────────────────────

class TimetablePage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        tk.Label(toolbar, text="Classe:", font=("Segoe UI", 10), bg=BG_DARK, fg=TEXT_SECONDARY).pack(side="left")
        self.class_var = tk.StringVar(value="CP")
        combo = ttk.Combobox(toolbar, textvariable=self.class_var, values=CLASSES,
                            state="readonly", width=8, font=("Segoe UI", 10))
        combo.pack(side="left", padx=5)
        combo.bind("<<ComboboxSelected>>", lambda e: self._load())
        ModernButton(toolbar, "➕  Ajouter Cours", self._add_slot, color=ACCENT_ORANGE).pack(side="left", padx=10)

        # Timetable grid
        grid_frame = Card(self, padx=10, pady=10)
        grid_frame.pack(fill="both", expand=True)

        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
        times = ["08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00",
                 "13:00-14:00", "14:00-15:00", "15:00-16:00", "16:00-17:00"]

        # Headers
        tk.Label(grid_frame, text="Heure", font=("Segoe UI", 9, "bold"),
                bg=BG_CARD, fg=ACCENT_ORANGE, width=12).grid(row=0, column=0, padx=2, pady=2, sticky="nsew")
        for col, day in enumerate(days):
            tk.Label(grid_frame, text=day, font=("Segoe UI", 9, "bold"),
                    bg=BG_CARD2, fg=ACCENT_ORANGE, width=12).grid(row=0, column=col+1, padx=2, pady=2, sticky="nsew")

        # Time slots
        self.slot_labels = {}
        for row, time in enumerate(times):
            tk.Label(grid_frame, text=time, font=("Segoe UI", 8, "bold"),
                    bg=BG_CARD, fg=TEXT_SECONDARY, width=12).grid(row=row+1, column=0, padx=2, pady=2, sticky="nsew")
            for col, day in enumerate(days):
                lbl = tk.Label(grid_frame, text="", font=("Segoe UI", 8),
                              bg=BG_CARD2, fg=TEXT_PRIMARY, width=12, height=2,
                              relief="flat", anchor="center")
                lbl.grid(row=row+1, column=col+1, padx=2, pady=2, sticky="nsew")
                self.slot_labels[(day, time)] = lbl
                grid_frame.grid_columnconfigure(col+1, weight=1)
            grid_frame.grid_rowconfigure(row+1, weight=1)

        self._load()

    def _load(self):
        # Clear
        for lbl in self.slot_labels.values():
            lbl.config(text="", bg=BG_CARD2)

        session = get_session()
        schedules = session.query(Schedule).filter_by(class_name=self.class_var.get()).all()
        colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE, ACCENT_YELLOW]
        
        for i, sched in enumerate(schedules):
            time_key = f"{sched.time_start}-{sched.time_end}"
            key = (sched.day, time_key)
            if key in self.slot_labels:
                color = colors[i % len(colors)]
                self.slot_labels[key].config(text=sched.subject or "", bg=color, fg=TEXT_PRIMARY)
        session.close()

    def _add_slot(self):
        TimetableSlotDialog(self, self.class_var.get(), self._load)


class TimetableSlotDialog(tk.Toplevel):
    def __init__(self, parent, class_name, on_save):
        super().__init__(parent)
        self.class_name = class_name
        self.on_save = on_save
        self.title("Ajouter un Cours")
        self.geometry("420x400")
        self.configure(bg=BG_DARK)
        self.grab_set()

        x = (self.winfo_screenwidth() - 420) // 2
        y = (self.winfo_screenheight() - 400) // 2
        self.geometry(f"420x400+{x}+{y}")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_ORANGE, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text=f"📅  Ajouter Cours - {self.class_name}", font=("Segoe UI", 12, "bold"),
                bg=ACCENT_ORANGE, fg=TEXT_PRIMARY).pack(anchor="w")

        form = tk.Frame(self, bg=BG_DARK, padx=25, pady=20)
        form.pack(fill="both", expand=True)

        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
        
        def lcombo(label, values, default=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            var = tk.StringVar(value=default)
            combo = ttk.Combobox(form, textvariable=var, values=values, state="readonly", font=("Segoe UI", 10))
            combo.pack(fill="x", pady=(2, 10), ipady=4)
            return var

        def lentry(label, default=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 10))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0)
            e.pack(fill="x", ipady=5)
            if default:
                e.insert(0, default)
            return e

        self.day_var = lcombo("Jour", days, "Lundi")
        self.start_var = lcombo("Heure Début", ["08:00","09:00","10:00","11:00","13:00","14:00","15:00","16:00"], "08:00")
        self.end_var = lcombo("Heure Fin", ["09:00","10:00","11:00","12:00","14:00","15:00","16:00","17:00"], "09:00")
        self.subject_entry = lentry("Matière", "")

        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x", pady=(10, 0))
        ModernButton(btn_frame, "💾  Enregistrer", self._save, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left", padx=10)

    def _save(self):
        subject = self.subject_entry.get().strip()
        if not subject:
            messagebox.showerror("Erreur", "La matière est obligatoire")
            return

        session = get_session()
        sched = Schedule(
            class_name=self.class_name,
            day=self.day_var.get(),
            time_start=self.start_var.get(),
            time_end=self.end_var.get(),
            subject=subject
        )
        session.add(sched)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", "Cours ajouté!")
        self.on_save()
        self.destroy()


# ─── DOCUMENTS PAGE ───────────────────────────────────────────────────────────

class DocumentsPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        toolbar = tk.Frame(self, bg=BG_DARK)
        toolbar.pack(fill="x", pady=(0, 15))

        ModernButton(toolbar, "📎  Importer Document", self._import, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(toolbar, "📂  Ouvrir", self._open, color=ACCENT_BLUE).pack(side="left", padx=5)
        ModernButton(toolbar, "🗑  Supprimer", self._delete, color=ACCENT_RED).pack(side="left")

        table_frame = Card(self, padx=0, pady=0)
        table_frame.pack(fill="both", expand=True)

        cols = ("name", "type", "related", "date", "notes")
        heads = ("Nom", "Type", "Lié à", "Date", "Notes")

        self.tree = StyledTreeview(table_frame, cols, heads)
        widths = [200, 120, 150, 120, 200]
        for col, w in zip(cols, widths):
            self.tree.column(col, width=w)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        from database.models import Document
        docs = session.query(Document).order_by(Document.uploaded_at.desc()).all()
        for i, doc in enumerate(docs):
            tag = "even" if i % 2 == 0 else "odd"
            related = ""
            if doc.student_id:
                s = session.query(Student).get(doc.student_id)
                related = f"Élève: {s.last_name} {s.first_name}" if s else ""
            self.tree.insert("", "end", iid=doc.id, tags=(tag,), values=(
                doc.name or "",
                doc.doc_type or "",
                related,
                doc.uploaded_at.strftime("%d/%m/%Y") if doc.uploaded_at else "",
                doc.notes or ""
            ))
        session.close()

    def _import(self):
        filepath = filedialog.askopenfilename(
            title="Importer un Document",
            filetypes=[("Tous fichiers", "*.*"), ("PDF", "*.pdf"), ("Images", "*.jpg *.png *.jpeg")]
        )
        if not filepath:
            return

        docs_dir = os.path.join(APP_DIR, "documents")
        os.makedirs(docs_dir, exist_ok=True)
        filename = os.path.basename(filepath)
        dest = os.path.join(docs_dir, filename)
        shutil.copy2(filepath, dest)

        session = get_session()
        from database.models import Document
        doc = Document(
            name=filename,
            doc_type="Autre",
            file_path=dest,
            notes=""
        )
        session.add(doc)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", f"Document importé: {filename}")
        self._load()

    def _open(self):
        sel = self.tree.selection()
        if not sel:
            return
        session = get_session()
        from database.models import Document
        doc = session.query(Document).get(int(sel[0]))
        if doc and doc.file_path and os.path.exists(doc.file_path):
            try:
                if sys.platform == "win32":
                    os.startfile(doc.file_path)
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.call(["open", doc.file_path])
                else:
                    import subprocess
                    subprocess.call(["xdg-open", doc.file_path])
            except Exception as e:
                messagebox.showerror("Erreur", str(e))
        else:
            messagebox.showwarning("Fichier", "Fichier introuvable")
        session.close()

    def _delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirmer", "Supprimer ce document ?"):
            session = get_session()
            from database.models import Document
            doc = session.query(Document).get(int(sel[0]))
            if doc:
                session.delete(doc)
                session.commit()
            session.close()
            self._load()


# ─── REPORTS PAGE ─────────────────────────────────────────────────────────────

class ReportsPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        tk.Label(self, text="📈  Générer des Rapports", font=("Segoe UI", 14, "bold"),
                bg=BG_DARK, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 20))

        cards_frame = tk.Frame(self, bg=BG_DARK)
        cards_frame.pack(fill="x", pady=(0, 20))

        reports = [
            ("📋  Liste des Élèves", "Exporter la liste complète des élèves en PDF", self._report_students, ACCENT_BLUE),
            ("💰  Rapport Financier", "Revenus, dépenses et bénéfices annuels", self._report_financial, ACCENT_GREEN),
            ("💳  Historique Paiements", "Tous les paiements avec détails", self._report_payments, ACCENT_ORANGE),
            ("👥  Liste Personnel", "Tous les employés et leurs salaires", self._report_employees, ACCENT_PURPLE),
        ]

        for i, (title, desc, cmd, color) in enumerate(reports):
            card = Card(cards_frame, padx=20, pady=20)
            card.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="nsew")
            cards_frame.grid_columnconfigure(i % 2, weight=1)

            tk.Label(card, text=title, font=("Segoe UI", 12, "bold"),
                    bg=BG_CARD, fg=color).pack(anchor="w")
            tk.Label(card, text=desc, font=("Segoe UI", 9),
                    bg=BG_CARD, fg=TEXT_SECONDARY, wraplength=250).pack(anchor="w", pady=(5, 15))
            ModernButton(card, "📥  Générer PDF", cmd, color=color).pack(anchor="w")

        # Summary stats
        summary_frame = Card(self, padx=20, pady=15)
        summary_frame.pack(fill="x")

        tk.Label(summary_frame, text="📊  Résumé de l'Année", font=("Segoe UI", 11, "bold"),
                bg=BG_CARD, fg=TEXT_PRIMARY).pack(anchor="w", pady=(0, 15))

        session = get_session()
        now = datetime.now()
        settings = get_settings()
        currency = settings.get("currency", "MAD")

        total_students = session.query(Student).filter_by(is_active=True).count()
        total_employees = session.query(Employee).filter_by(is_active=True).count()
        
        year_pay = session.query(Payment).filter(Payment.payment_date >= datetime(now.year,1,1)).all()
        total_revenue = sum(p.amount for p in year_pay)
        
        year_exp = session.query(Expense).filter(Expense.date >= date(now.year,1,1)).all()
        total_expenses = sum(e.amount for e in year_exp)
        session.close()

        for label, val in [
            ("Élèves actifs", f"{total_students}"),
            ("Personnel actif", f"{total_employees}"),
            (f"Revenu {now.year}", f"{total_revenue:,.2f} {currency}"),
            (f"Dépenses {now.year}", f"{total_expenses:,.2f} {currency}"),
            (f"Bénéfice {now.year}", f"{total_revenue - total_expenses:,.2f} {currency}"),
        ]:
            row = tk.Frame(summary_frame, bg=BG_CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_SECONDARY, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=("Segoe UI", 9, "bold"), bg=BG_CARD, fg=TEXT_PRIMARY).pack(side="left")

    def _report_students(self):
        self._generate_students_pdf()

    def _report_financial(self):
        self._generate_financial_pdf()

    def _report_payments(self):
        self._generate_payments_pdf()

    def _report_employees(self):
        self._generate_employees_pdf()

    def _generate_students_pdf(self):
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="liste_eleves.pdf"
        )
        if not path:
            return

        session = get_session()
        students = session.query(Student).filter_by(is_active=True).order_by(Student.class_name, Student.last_name).all()
        session.close()

        doc = SimpleDocTemplate(path, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        story = []

        settings = get_settings()
        story.append(Paragraph(settings.get("school_name", "Le Schéma"), styles["Title"]))
        story.append(Paragraph(f"Liste des Élèves - {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
        story.append(Spacer(1, 20))

        data = [["Code", "Nom", "Prénom", "Classe", "Parent", "Téléphone", "Transport", "Assurance", "Mensualité"]]
        for s in students:
            data.append([
                s.student_code or "",
                s.last_name or "",
                s.first_name or "",
                s.class_name or "",
                s.parent_name or "",
                s.parent_phone or "",
                "Oui" if s.transport else "Non",
                "Oui" if s.insurance_paid else "Non",
                f"{s.monthly_fee:.0f}"
            ])

        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF6B00")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        doc.build(story)

        messagebox.showinfo("Succès", f"Rapport généré: {path}")
        try:
            if sys.platform == "win32":
                os.startfile(path)
        except Exception:
            pass

    def _generate_financial_pdf(self):
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="rapport_financier.pdf"
        )
        if not path:
            return

        session = get_session()
        now = datetime.now()
        settings = get_settings()
        currency = settings.get("currency", "MAD")

        payments = session.query(Payment).filter(Payment.payment_date >= datetime(now.year,1,1)).all()
        expenses = session.query(Expense).filter(Expense.date >= date(now.year,1,1)).all()
        session.close()

        total_rev = sum(p.amount for p in payments)
        total_exp = sum(e.amount for e in expenses)
        profit = total_rev - total_exp

        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(settings.get("school_name", "Le Schéma"), styles["Title"]))
        story.append(Paragraph(f"Rapport Financier {now.year}", styles["Heading2"]))
        story.append(Spacer(1, 20))

        data = [
            ["Indicateur", "Montant"],
            ["Total Revenus", f"{total_rev:,.2f} {currency}"],
            ["Total Dépenses", f"{total_exp:,.2f} {currency}"],
            ["Bénéfice Net", f"{profit:,.2f} {currency}"],
        ]
        t = Table(data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF6B00")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(t)
        doc.build(story)

        messagebox.showinfo("Succès", f"Rapport financier généré: {path}")

    def _generate_payments_pdf(self):
        messagebox.showinfo("En cours", "Rapport des paiements en cours de génération...")

    def _generate_employees_pdf(self):
        messagebox.showinfo("En cours", "Rapport du personnel en cours de génération...")


# ─── SETTINGS PAGE ────────────────────────────────────────────────────────────

class SettingsPage(tk.Frame):
    def __init__(self, parent, user, app):
        super().__init__(parent, bg=BG_DARK)
        self.user = user
        self.app = app
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        form = tk.Frame(canvas, bg=BG_DARK, padx=0, pady=0)
        cw = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=canvas.winfo_width()))

        settings = get_settings()
        self.fields = {}

        def section(title, icon):
            tk.Label(form, text=f"{icon}  {title}", font=("Segoe UI", 12, "bold"),
                    bg=BG_DARK, fg=ACCENT_ORANGE, pady=10).pack(anchor="w")
            sec = Card(form, padx=20, pady=15)
            sec.pack(fill="x", pady=(0, 15))
            return sec

        def labeled_entry(parent, label, key, value=""):
            tk.Label(parent, text=label, font=("Segoe UI", 9), bg=BG_CARD, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(parent, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 12))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0)
            e.pack(fill="x", ipady=5)
            if value:
                e.insert(0, str(value))
            self.fields[key] = e

        # School info
        school_sec = section("Informations de l'École", "🏫")
        labeled_entry(school_sec, "Nom de l'École", "school_name", settings.get("school_name", ""))
        labeled_entry(school_sec, "Slogan", "school_slogan", settings.get("school_slogan", ""))
        labeled_entry(school_sec, "Adresse", "school_address", settings.get("school_address", ""))
        labeled_entry(school_sec, "Téléphone", "school_phone", settings.get("school_phone", ""))
        labeled_entry(school_sec, "Email", "school_email", settings.get("school_email", ""))
        labeled_entry(school_sec, "Site Web", "school_website", settings.get("school_website", ""))
        labeled_entry(school_sec, "Année Scolaire", "current_year", settings.get("current_year", "2025-2026"))

        # Financial settings
        fin_sec = section("Paramètres Financiers", "💰")
        labeled_entry(fin_sec, "Devise", "currency", settings.get("currency", "MAD"))
        labeled_entry(fin_sec, "Frais d'Assurance (MAD)", "insurance_fee", settings.get("insurance_fee", "500"))
        labeled_entry(fin_sec, "Frais de Transport (MAD)", "transport_fee", settings.get("transport_fee", "300"))

        # User management
        user_sec = section("Gestion des Utilisateurs", "👥")
        if self.user.get("role") == "Admin":
            ModernButton(user_sec, "👤  Gérer les Utilisateurs", self._manage_users, color=ACCENT_BLUE).pack(anchor="w")
        else:
            tk.Label(user_sec, text="Accès Admin requis", font=("Segoe UI", 9),
                    bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")

        # Backup
        backup_sec = section("Sauvegarde & Restauration", "💾")
        btn_frame = tk.Frame(backup_sec, bg=BG_CARD)
        btn_frame.pack(anchor="w")
        ModernButton(btn_frame, "💾  Sauvegarder maintenant", self._backup, color=ACCENT_GREEN).pack(side="left")
        ModernButton(btn_frame, "📂  Restaurer", self._restore, color=ACCENT_ORANGE).pack(side="left", padx=10)

        # Save button
        ModernButton(form, "💾  Enregistrer les Paramètres", self._save, color=ACCENT_ORANGE, font_size=12).pack(
            fill="x", pady=(10, 0), ipady=5)

    def _save(self):
        for key, widget in self.fields.items():
            val = widget.get().strip()
            if val:
                save_setting(key, val)
        messagebox.showinfo("Succès", "Paramètres enregistrés avec succès!")

    def _manage_users(self):
        UserManagementDialog(self)

    def _backup(self):
        db_path = os.path.join(APP_DIR, "data", "school.db")
        if not os.path.exists(db_path):
            messagebox.showerror("Erreur", "Base de données introuvable")
            return

        backups_dir = os.path.join(APP_DIR, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(backups_dir, backup_name)
        
        shutil.copy2(db_path, backup_path)
        
        session = get_session()
        backup = Backup(
            filename=backup_name,
            file_path=backup_path,
            size_bytes=os.path.getsize(backup_path),
            created_by=self.user.get("username", "admin")
        )
        session.add(backup)
        session.commit()
        session.close()

        messagebox.showinfo("Sauvegarde", f"✅ Sauvegarde créée:\n{backup_name}")

    def _restore(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner une sauvegarde",
            filetypes=[("SQLite DB", "*.db"), ("Tous fichiers", "*.*")],
            initialdir=os.path.join(APP_DIR, "backups")
        )
        if not filepath:
            return
        
        if messagebox.askyesno("Restaurer", "⚠️ Ceci remplacera la base de données actuelle. Continuer ?"):
            db_path = os.path.join(APP_DIR, "data", "school.db")
            shutil.copy2(filepath, db_path)
            messagebox.showinfo("Restauration", "✅ Base de données restaurée. Redémarrez l'application.")


class UserManagementDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gestion des Utilisateurs")
        self.geometry("600x500")
        self.configure(bg=BG_DARK)
        self.grab_set()

        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"600x500+{x}+{y}")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_PURPLE, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="👥  Gestion des Utilisateurs", font=("Segoe UI", 13, "bold"),
                bg=ACCENT_PURPLE, fg=TEXT_PRIMARY).pack(anchor="w")

        toolbar = tk.Frame(self, bg=BG_DARK, padx=15, pady=10)
        toolbar.pack(fill="x")
        ModernButton(toolbar, "➕  Ajouter", self._add_user, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(toolbar, "🗑  Supprimer", self._delete_user, color=ACCENT_RED).pack(side="left", padx=5)

        table_frame = tk.Frame(self, bg=BG_DARK, padx=15)
        table_frame.pack(fill="both", expand=True)

        cols = ("username", "full_name", "role", "last_login", "active")
        heads = ("Utilisateur", "Nom Complet", "Rôle", "Dernière Connexion", "Statut")
        self.tree = StyledTreeview(table_frame, cols, heads)
        for col, w in zip(cols, [120, 150, 100, 150, 80]):
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True)

        self._load()

    def _load(self):
        self.tree.delete(*self.tree.get_children())
        session = get_session()
        users = session.query(User).all()
        for i, u in enumerate(users):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=u.id, tags=(tag,), values=(
                u.username, u.full_name or "", u.role,
                u.last_login.strftime("%d/%m/%Y %H:%M") if u.last_login else "Jamais",
                "✅ Actif" if u.is_active else "❌ Inactif"
            ))
        session.close()

    def _add_user(self):
        AddUserDialog(self, self._load)

    def _delete_user(self):
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirmer", "Désactiver cet utilisateur ?"):
            session = get_session()
            u = session.query(User).get(int(sel[0]))
            if u:
                u.is_active = False
                session.commit()
            session.close()
            self._load()


class AddUserDialog(tk.Toplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Ajouter Utilisateur")
        self.geometry("400x420")
        self.configure(bg=BG_DARK)
        self.grab_set()
        
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 420) // 2
        self.geometry(f"400x420+{x}+{y}")
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=ACCENT_ORANGE, padx=20, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="👤  Nouvel Utilisateur", font=("Segoe UI", 12, "bold"),
                bg=ACCENT_ORANGE, fg=TEXT_PRIMARY).pack(anchor="w")

        form = tk.Frame(self, bg=BG_DARK, padx=25, pady=20)
        form.pack(fill="both", expand=True)

        self.fields = {}

        def lentry(label, key, show=""):
            tk.Label(form, text=label, font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
            ef = tk.Frame(form, bg=BG_CARD2, padx=10, pady=3)
            ef.pack(fill="x", pady=(2, 12))
            e = tk.Entry(ef, bg=BG_CARD2, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 10), bd=0, show=show)
            e.pack(fill="x", ipady=5)
            self.fields[key] = e

        lentry("Nom d'utilisateur", "username")
        lentry("Nom Complet", "full_name")
        lentry("Mot de passe", "password", show="●")
        lentry("Confirmer Mot de passe", "confirm_password", show="●")

        tk.Label(form, text="Rôle", font=("Segoe UI", 9), bg=BG_DARK, fg=TEXT_SECONDARY).pack(anchor="w")
        self.role_var = tk.StringVar(value="Secrétaire")
        role_combo = ttk.Combobox(form, textvariable=self.role_var,
                                   values=["Admin", "Comptable", "Secrétaire"],
                                   state="readonly", font=("Segoe UI", 10))
        role_combo.pack(fill="x", pady=(2, 12), ipady=4)

        btn_frame = tk.Frame(form, bg=BG_DARK)
        btn_frame.pack(fill="x")
        ModernButton(btn_frame, "💾  Créer", self._save, color=ACCENT_ORANGE).pack(side="left")
        ModernButton(btn_frame, "✖  Annuler", self.destroy, color=BG_CARD2).pack(side="left", padx=10)

    def _save(self):
        username = self.fields["username"].get().strip()
        full_name = self.fields["full_name"].get().strip()
        password = self.fields["password"].get()
        confirm = self.fields["confirm_password"].get()

        if not username or not password:
            messagebox.showerror("Erreur", "Nom d'utilisateur et mot de passe requis")
            return
        if password != confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return

        session = get_session()
        if session.query(User).filter_by(username=username).first():
            messagebox.showerror("Erreur", "Ce nom d'utilisateur existe déjà")
            session.close()
            return

        user = User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            role=self.role_var.get(),
            is_active=True
        )
        session.add(user)
        session.commit()
        session.close()

        messagebox.showinfo("Succès", "Utilisateur créé avec succès!")
        self.on_save()
        self.destroy()


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = SchoolApp()
    app.run()
