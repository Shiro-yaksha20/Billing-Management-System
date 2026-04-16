"""ORM models for the salon billing database."""

from __future__ import annotations

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created/updated timestamps."""

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Staff(Base, TimestampMixin):
    """Staff member record."""

    __tablename__ = "staff"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(String)
    active = Column(Boolean, default=True)

    bills = relationship("Bill", back_populates="staff")


class Service(Base, TimestampMixin):
    """Service catalog record."""

    __tablename__ = "service"
    id = Column(Integer, primary_key=True)
    category = Column(String)  # e.g., "Basic", "Facial", "Bridal"
    name = Column(String, nullable=False)
    variant = Column(String)  # e.g., "Short", "Medium", "Long", "Honey", "Rica"
    display_name = Column(String)  # Full formatted name for display
    description = Column(String)
    price = Column(Numeric(10, 2))
    duration_minutes = Column(Integer)
    notes = Column(Text)  # Pricing notes, special instructions
    active = Column(Boolean, default=True)


class Customer(Base, TimestampMixin):
    """Customer record."""

    __tablename__ = "customer"
    __table_args__ = (
        Index("ix_customer_phone", "phone"),
        Index("ix_customer_name", "name"),
    )
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    notes = Column(Text)
    last_visit_at = Column(DateTime)

    bills = relationship("Bill", back_populates="customer")


class Bill(Base, TimestampMixin):
    """Bill header record."""

    __tablename__ = "bill"
    __table_args__ = (
        Index("ix_bill_datetime", "bill_datetime"),
        Index("ix_bill_customer_id", "customer_id"),
        Index("ix_bill_payment_status", "payment_status"),
    )
    id = Column(Integer, primary_key=True)
    bill_number = Column(String, unique=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    bill_datetime = Column(DateTime, default=datetime.datetime.utcnow)
    subtotal = Column(Numeric(10, 2))
    discount_amount = Column(Numeric(10, 2), default=0)
    discount_type = Column(Enum("flat", "percent", "none", name="discount_type_enum"), default="none")
    tax_amount = Column(Numeric(10, 2), default=0)
    tax_percent = Column(Numeric(5, 2))
    total = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum("Cash", "UPI", "Card", "Other", name="payment_method_enum"), default="Cash")
    status = Column(Enum("Paid", "Pending", "Cancelled", name="status_enum"), default="Paid")
    pdf_path = Column(String)
    whatsapp_status = Column(Enum("Not Sent", "Sent", "Failed", name="whatsapp_status_enum"), default="Not Sent")
    whatsapp_last_error = Column(Text)
    transaction_id = Column(String)  # UPI/Card transaction reference
    payment_status = Column(String, default="Paid")  # Redundant with status enum, used for receipt display

    customer = relationship("Customer", back_populates="bills")
    staff = relationship("Staff", back_populates="bills")
    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")


class BillItem(Base):
    """Bill line item record."""

    __tablename__ = "bill_item"
    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bill.id"))
    service_id = Column(Integer, ForeignKey("service.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2))
    line_total = Column(Numeric(10, 2))

    bill = relationship("Bill", back_populates="items")
    service = relationship("Service")


class Setting(Base):
    """Application setting record."""

    __tablename__ = "setting"
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
