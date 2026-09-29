from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class BusinessCreate(BaseModel):
    name: str
    slug: str


class BusinessOut(BaseModel):
    id: str
    name: str
    slug: str
    color: str
    stamps_total: int
    reward: str
    daily_limit: int
    whatsapp: str
    admin_key: Optional[str] = None  # solo se devuelve al crear el negocio

    class Config:
        from_attributes = True


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    stamps_total: Optional[int] = None
    reward: Optional[str] = None
    daily_limit: Optional[int] = None
    whatsapp: Optional[str] = None


class CustomerCreate(BaseModel):
    name: str
    phone: str = ""


class CustomerOut(BaseModel):
    id: str
    name: str
    phone: str
    stamps: int
    rewards_claimed: int

    class Config:
        from_attributes = True


class StampAction(BaseModel):
    customer_id: str


class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str = "General"


class MenuItemOut(BaseModel):
    id: str
    name: str
    price: float
    category: str
    active: bool

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    name: str
    qty: int
    price: float


class OrderCreate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: str
    mode: str = "Retiro"
    note: str = ""
    items: List[OrderItem]


class OrderOut(BaseModel):
    id: int
    customer_id: Optional[str]
    customer_name: str
    mode: str
    note: str
    items: List[OrderItem]
    total: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
