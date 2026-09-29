import json
import secrets
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sellos API")

# En producción, reemplazar "*" por el dominio real del frontend (GitHub Pages, etc).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_business_by_slug(db: Session, slug: str) -> models.Business:
    b = db.query(models.Business).filter(models.Business.slug == slug).first()
    if not b:
        raise HTTPException(404, "Negocio no encontrado")
    return b


def require_admin(business: models.Business, x_admin_key: Optional[str]):
    if not x_admin_key or x_admin_key != business.admin_key:
        raise HTTPException(401, "Clave de administrador inválida")


# ---------- Negocios ----------

@app.post("/businesses", response_model=schemas.BusinessOut)
def create_business(data: schemas.BusinessCreate, db: Session = Depends(get_db)):
    if db.query(models.Business).filter(models.Business.slug == data.slug).first():
        raise HTTPException(400, "Ese identificador ya está en uso")
    b = models.Business(name=data.name, slug=data.slug, admin_key=secrets.token_hex(8))
    db.add(b)
    db.commit()
    db.refresh(b)
    return b  # admin_key va incluida solo en esta respuesta: guardarla, no se vuelve a mostrar


@app.get("/businesses/{slug}", response_model=schemas.BusinessOut)
def get_business(slug: str, db: Session = Depends(get_db)):
    b = get_business_by_slug(db, slug)
    out = schemas.BusinessOut.model_validate(b)
    out.admin_key = None
    return out


@app.patch("/businesses/{slug}", response_model=schemas.BusinessOut)
def update_business(
    slug: str, data: schemas.BusinessUpdate, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    out = schemas.BusinessOut.model_validate(b)
    out.admin_key = None
    return out


# ---------- Clientes ----------

@app.post("/businesses/{slug}/customers", response_model=schemas.CustomerOut)
def create_customer(slug: str, data: schemas.CustomerCreate, db: Session = Depends(get_db)):
    b = get_business_by_slug(db, slug)
    c = models.Customer(business_id=b.id, name=data.name, phone=data.phone)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.get("/businesses/{slug}/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer(slug: str, customer_id: str, db: Session = Depends(get_db)):
    b = get_business_by_slug(db, slug)
    c = db.query(models.Customer).filter_by(business_id=b.id, id=customer_id).first()
    if not c:
        raise HTTPException(404, "Cliente no encontrado")
    return c


@app.get("/businesses/{slug}/customers", response_model=List[schemas.CustomerOut])
def list_customers(
    slug: str, db: Session = Depends(get_db), x_admin_key: Optional[str] = Header(None)
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    return db.query(models.Customer).filter_by(business_id=b.id).order_by(models.Customer.created_at.desc()).all()


# ---------- Sellos ----------

@app.post("/businesses/{slug}/stamp", response_model=schemas.CustomerOut)
def add_stamp(
    slug: str, data: schemas.StampAction, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    c = db.query(models.Customer).filter_by(business_id=b.id, id=data.customer_id).first()
    if not c:
        raise HTTPException(404, "Cliente no encontrado")
    if c.stamps >= b.stamps_total:
        raise HTTPException(400, "Este cliente ya completó la tarjeta. Canjeá la recompensa primero.")
    today_count = (
        db.query(models.StampLog)
        .filter_by(customer_id=c.id, status="ok", day=date.today())
        .count()
    )
    if today_count >= b.daily_limit:
        raise HTTPException(400, f"Límite diario alcanzado ({b.daily_limit} por día).")
    c.stamps += 1
    db.add(models.StampLog(customer_id=c.id, business_id=b.id, day=date.today()))
    db.commit()
    db.refresh(c)
    return c


@app.post("/businesses/{slug}/redeem", response_model=schemas.CustomerOut)
def redeem(
    slug: str, data: schemas.StampAction, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    c = db.query(models.Customer).filter_by(business_id=b.id, id=data.customer_id).first()
    if not c:
        raise HTTPException(404, "Cliente no encontrado")
    if c.stamps < b.stamps_total:
        raise HTTPException(400, "Todavía no completó la tarjeta.")
    c.stamps = 0
    c.rewards_claimed += 1
    db.commit()
    db.refresh(c)
    return c


# ---------- Menú ----------

@app.get("/businesses/{slug}/menu", response_model=List[schemas.MenuItemOut])
def list_menu(slug: str, db: Session = Depends(get_db)):
    b = get_business_by_slug(db, slug)
    return db.query(models.MenuItem).filter_by(business_id=b.id, active=True).all()


@app.post("/businesses/{slug}/menu", response_model=schemas.MenuItemOut)
def add_menu_item(
    slug: str, data: schemas.MenuItemCreate, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    m = models.MenuItem(business_id=b.id, name=data.name, price=data.price, category=data.category)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@app.delete("/businesses/{slug}/menu/{item_id}")
def remove_menu_item(
    slug: str, item_id: str, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    m = db.query(models.MenuItem).filter_by(business_id=b.id, id=item_id).first()
    if not m:
        raise HTTPException(404, "Producto no encontrado")
    m.active = False
    db.commit()
    return {"ok": True}


# ---------- Pedidos ----------

def _order_out(o: models.Order) -> schemas.OrderOut:
    return schemas.OrderOut(
        id=o.id, customer_id=o.customer_id, customer_name=o.customer_name,
        mode=o.mode, note=o.note, items=json.loads(o.items_json),
        total=o.total, status=o.status, created_at=o.created_at,
    )


@app.post("/businesses/{slug}/orders", response_model=schemas.OrderOut)
def create_order(slug: str, data: schemas.OrderCreate, db: Session = Depends(get_db)):
    b = get_business_by_slug(db, slug)
    total = sum(i.qty * i.price for i in data.items)
    o = models.Order(
        business_id=b.id, customer_id=data.customer_id, customer_name=data.customer_name,
        mode=data.mode, note=data.note, items_json=json.dumps([i.model_dump() for i in data.items]),
        total=total,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return _order_out(o)


@app.get("/businesses/{slug}/orders", response_model=List[schemas.OrderOut])
def list_orders(
    slug: str, db: Session = Depends(get_db), x_admin_key: Optional[str] = Header(None)
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    orders = db.query(models.Order).filter_by(business_id=b.id).order_by(models.Order.created_at.desc()).all()
    return [_order_out(o) for o in orders]


@app.post("/businesses/{slug}/orders/{order_id}/deliver", response_model=schemas.OrderOut)
def deliver_order(
    slug: str, order_id: int, db: Session = Depends(get_db),
    x_admin_key: Optional[str] = Header(None),
):
    b = get_business_by_slug(db, slug)
    require_admin(b, x_admin_key)
    o = db.query(models.Order).filter_by(business_id=b.id, id=order_id).first()
    if not o:
        raise HTTPException(404, "Pedido no encontrado")
    o.status = "entregado"
    db.commit()
    db.refresh(o)
    return _order_out(o)


@app.get("/")
def root():
    return {"status": "ok", "service": "sellos-api"}
