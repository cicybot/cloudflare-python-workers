from app import app
from routers import personal

app.include_router(personal.router)
