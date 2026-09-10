"""LifeOS FastAPI Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import auth, bills, obligations, insurance, properties, maintenance, health, documents, dashboard, calendar, reports, search, notifications, settings as settings_router, voice_agent, voice_ws, users

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(bills.router)
app.include_router(obligations.router)
app.include_router(insurance.router)
app.include_router(properties.router)
app.include_router(maintenance.router)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(calendar.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)
app.include_router(voice_agent.router)
app.include_router(voice_ws.router)
app.include_router(users.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
def root():
    return {"app": "LifeOS API", "docs": "/docs"}