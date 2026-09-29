import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# En Render: configurar DATABASE_URL con la conexión de Postgres.
# En local, si no está definida, usa un archivo SQLite (sellos.db).
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sellos.db")

# SQLAlchemy 2.1+ interpreta "postgresql://" como el driver psycopg (v3) por
# defecto. Como instalamos psycopg2-binary, forzamos ese driver explícito.
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
