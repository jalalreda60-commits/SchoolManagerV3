"""
Database Models for Le Schéma School Management System
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

CLASSES = ["PS", "MS", "GS", "CP", "CE1", "CE2", "CM1", "CM2", "6EME", "1AC", "2AC", "3AC", "TC", "1BAC", "2BAC"]
ROLES = ["Admin", "Comptable", "Secrétaire"]


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)
    full_name = Column(String(100))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    student_code = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    photo_path = Column(String(256))
    gender = Column(String(10))
    birth_date = Column(Date)
    address = Column(Text)
    parent_name = Column(String(100))
    parent_phone = Column(String(20))
    emergency_phone = Column(String(20))
    class_name = Column(String(10))
    registration_date = Column(Date, default=datetime.now().date)
    transport = Column(Boolean, default=False)
    insurance_paid = Column(Boolean, default=False)
    monthly_fee = Column(Float, default=0.0)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    payments = relationship("Payment", back_populates="student")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(20), unique=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    payment_type = Column(String(20))  # monthly, insurance, transport
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    month = Column(String(20))
    year = Column(Integer)
    notes = Column(Text)
    receipt_path = Column(String(256))
    created_by = Column(String(50))

    student = relationship("Student", back_populates="payments")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    employee_code = Column(String(20), unique=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role = Column(String(50))  # teacher, admin, driver, etc.
    subject = Column(String(50))  # for teachers
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    hire_date = Column(Date)
    base_salary = Column(Float, default=0.0)
    cin = Column(String(20))
    cin_scan_path = Column(String(256))
    contract_path = Column(String(256))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    salaries = relationship("Salary", back_populates="employee")


class Salary(Base):
    __tablename__ = "salaries"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    month = Column(String(20))
    year = Column(Integer)
    base_amount = Column(Float)
    bonus = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_amount = Column(Float)
    paid = Column(Boolean, default=False)
    paid_date = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

    employee = relationship("Employee", back_populates="salaries")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True)
    category = Column(String(50))
    description = Column(Text)
    amount = Column(Float, nullable=False)
    expense_type = Column(String(20))  # fixed, variable
    date = Column(Date, default=datetime.now().date)
    receipt_path = Column(String(256))
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)


class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True)
    bus_number = Column(String(20), unique=True)
    plate_number = Column(String(20))
    capacity = Column(Integer)
    driver_id = Column(Integer, ForeignKey("employees.id"))
    route = Column(Text)
    is_active = Column(Boolean, default=True)


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True)
    class_name = Column(String(10))
    day = Column(String(10))
    time_start = Column(String(10))
    time_end = Column(String(10))
    subject = Column(String(50))
    teacher_id = Column(Integer, ForeignKey("employees.id"))
    room = Column(String(20))


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    doc_type = Column(String(50))
    file_path = Column(String(256))
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.now)
    notes = Column(Text)


class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)


class Backup(Base):
    __tablename__ = "backups"
    id = Column(Integer, primary_key=True)
    filename = Column(String(100))
    file_path = Column(String(256))
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String(50))


def init_database():
    """Initialize database and create tables"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "school.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session()


def get_session():
    _, session = init_database()
    return session
