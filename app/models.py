import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def uid():
    return uuid.uuid4().hex[:12]


class Business(Base):
    __tablename__ = "businesses"
    id = Column(String, primary_key=True, default=uid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    admin_key = Column(String, nullable=False)  # clave simple para el panel del negocio
    color = Column(String, default="#0f5c4d")
    stamps_total = Column(Integer, default=6)
    reward = Column(String, default="1 producto gratis")
    daily_limit = Column(Integer, default=1)
    whatsapp = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    customers = relationship("Customer", back_populates="business", cascade="all,delete")
    menu_items = relationship("MenuItem", back_populates="business", cascade="all,delete")
    orders = relationship("Order", back_populates="business", cascade="all,delete")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=uid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    stamps = Column(Integer, default=0)
    rewards_claimed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="customers")
    logs = relationship("StampLog", back_populates="customer", cascade="all,delete")


class StampLog(Base):
    __tablename__ = "stamp_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    day = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ok")  # ok | void

    customer = relationship("Customer", back_populates="logs")


class MenuItem(Base):
    __tablename__ = "menu_items"
    id = Column(String, primary_key=True, default=uid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String, default="General")
    active = Column(Boolean, default=True)

    business = relationship("Business", back_populates="menu_items")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String, nullable=False)
    mode = Column(String, default="Retiro")
    note = Column(Text, default="")
    items_json = Column(Text, nullable=False)  # [{"name":..,"qty":..,"price":..}]
    total = Column(Float, default=0)
    status = Column(String, default="nuevo")  # nuevo | entregado
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="orders")
