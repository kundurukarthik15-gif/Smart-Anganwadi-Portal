# ================================================================
#  SMART ANGANWADI PORTAL — models.py
#  SQLAlchemy Models matching Supabase Database Schema
# ================================================================

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Center(Base):
    __tablename__ = 'centers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    center_name = Column(String(255), nullable=False)
    district = Column(String(100), nullable=False)
    mandal = Column(String(100), nullable=False)
    village = Column(String(100), nullable=False)
    address = Column(Text)
    mobile = Column(String(15))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="center", cascade="all, delete-orphan")
    children = relationship("Child", back_populates="center", cascade="all, delete-orphan")
    beneficiaries = relationship("Beneficiary", back_populates="center", cascade="all, delete-orphan")
    stock_entries = relationship("StockEntry", back_populates="center", cascade="all, delete-orphan")
    bmi_records = relationship("BmiRecord", back_populates="center", cascade="all, delete-orphan")
    village_surveys = relationship("VillageSurvey", back_populates="center", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="center", cascade="all, delete-orphan")
    villagers = relationship("Villager", back_populates="center", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    mobile = Column(String(15))
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="users")

class Child(Base):
    __tablename__ = 'children'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    parent_name = Column(String(255))
    parent_mobile = Column(String(15))
    address = Column(Text)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="children")
    attendance_records = relationship("Attendance", back_populates="child", cascade="all, delete-orphan")
    bmi_records = relationship("BmiRecord", back_populates="child")

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey('children.id', ondelete='CASCADE'), nullable=False)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    attendance_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    status = Column(String(20), nullable=False)  # 'Present', 'Absent'
    photo_url = Column(String(2048))
    recorded_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('child_id', 'attendance_date', name='attendance_unique_daily_record'),)
    
    # Relationships
    child = relationship("Child", back_populates="attendance_records")

class Beneficiary(Base):
    __tablename__ = 'beneficiaries'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # 'Pregnant Woman', 'Lactating Mother'
    mobile = Column(String(15))
    address = Column(Text)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="beneficiaries")

class StockEntry(Base):
    __tablename__ = 'stock_entries'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String(255), nullable=False)
    quantity_received = Column(Numeric(10, 2), default=0.0)
    quantity_distributed = Column(Numeric(10, 2), default=0.0)
    remaining_quantity = Column(Numeric(10, 2), default=0.0)
    min_quantity = Column(Numeric(10, 2), default=20.0)
    unit = Column(String(50), default='units')
    received_date = Column(Date)
    supplier = Column(String(255))
    notes = Column(Text)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('center_id', 'item_name', name='unique_center_item'),)
    
    # Relationships
    center = relationship("Center", back_populates="stock_entries")

class StockDistribution(Base):
    __tablename__ = 'stock_distribution'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stock_id = Column(String(36), ForeignKey('stock_entries.id', ondelete='SET NULL'))
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    distributed_to = Column(String(255), nullable=False)
    distribution_date = Column(Date)
    distributed_by = Column(String(255))
    beneficiary_id = Column(String(36), ForeignKey('beneficiaries.id', ondelete='SET NULL'))
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class BmiRecord(Base):
    __tablename__ = 'bmi_records'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    child_id = Column(String(36), ForeignKey('children.id', ondelete='SET NULL'))
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    recorded_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'))
    child_name = Column(String(255), nullable=False)
    age_at_measurement = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    height_cm = Column(Numeric(5, 1), nullable=False)
    weight_kg = Column(Numeric(5, 2), nullable=False)
    bmi_value = Column(Numeric(5, 2), nullable=False)
    bmi_category = Column(String(30), nullable=False)  # 'Severe Underweight', 'Underweight', 'Normal', 'Overweight', 'Obese'
    nutrition_status = Column(Text)
    ai_recommendation = Column(Text) # Stored as JSON string or text
    measurement_date = Column(Date, nullable=False, default=datetime.utcnow().date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (UniqueConstraint('child_id', 'measurement_date', name='unique_daily_bmi'),)
    
    # Relationships
    center = relationship("Center", back_populates="bmi_records")
    child = relationship("Child", back_populates="bmi_records")

class Story(Base):
    __tablename__ = 'stories'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    language = Column(String(20), nullable=False)  # 'English', 'Telugu', 'Hindi'
    category = Column(String(100), default='Moral Stories')
    emoji = Column(String(10), default='📖')
    preview = Column(Text)
    has_audio = Column(Boolean, default=False)
    pdf_url = Column(Text)
    audio_url = Column(Text)
    video_url = Column(Text)
    youtube_url = Column(Text)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    uploaded_by = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class VillageSurvey(Base):
    __tablename__ = 'village_survey'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    village_name = Column(String(255), nullable=False)
    total_population = Column(Integer, nullable=False)
    total_families = Column(Integer, nullable=False)
    total_children = Column(Integer, nullable=False)
    pregnant_women = Column(Integer, nullable=False)
    lactating_mothers = Column(Integer, nullable=False)
    survey_year = Column(Integer, nullable=False)
    survey_month = Column(Integer)  # Nullable for yearly surveys
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="village_surveys")

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = Column(String(100), nullable=False)
    pdf_url = Column(Text, nullable=False)
    generated_by = Column(String(255), nullable=False)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="reports")

class Villager(Base):
    __tablename__ = 'villagers'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    category = Column(String(50), nullable=False)  # 'Child', 'Pregnant Woman', 'Lactating Mother', 'General Resident'
    contact_number = Column(String(15))
    address = Column(Text)
    center_id = Column(String(36), ForeignKey('centers.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    center = relationship("Center", back_populates="villagers")
