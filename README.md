# Sellos API

Backend en FastAPI para la app de fidelización + catálogo de pedidos.
Multi-negocio: cada negocio tiene un `slug` (identificador en la URL) y una
`admin_key` (clave para las acciones del panel: sellar, ver pedidos, editar menú).

## Probar en local

```
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload
```

Abrir http://127.0.0.1:8000/docs para ver y probar todos los endpoints.

## Desplegar en Render (igual que lector-facturas-py)

1. Subir esta carpeta a un repo de GitHub.
2. En Render: New > Web Service, conectar el repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Agregar una base de datos Postgres en Render (New > PostgreSQL) y copiar su
   "Internal Database URL" como variable de entorno `DATABASE_URL` del web service.
   Sin esa variable, el backend usa SQLite en un archivo local (sirve para probar,
   pero se borra en cada despliegue).

## Flujo básico

1. `POST /businesses` con `{"name": "...", "slug": "..."}` crea el negocio y
   devuelve una `admin_key` — guardarla, no se vuelve a mostrar.
2. El frontend público (cliente) usa `slug` para leer negocio, menú, y crear
   clientes/pedidos: no necesita la `admin_key`.
3. El panel del negocio manda la `admin_key` en el header `X-Admin-Key` para
   sellar, canjear, ver pedidos y editar el menú.
