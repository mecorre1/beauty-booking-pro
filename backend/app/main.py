from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    admin_auth,
    admin_bookings,
    admin_salon,
    admin_schedule,
    admin_services,
    public_booking,
)
from app.db import init_db


def create_app(*, init_db_on_startup: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if init_db_on_startup:
            init_db()
        yield

    application = FastAPI(title="Beauty Booking API", version="0.1.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(public_booking.router, prefix="/api/public", tags=["public"])
    application.include_router(admin_auth.router, prefix="/api/admin/auth", tags=["admin-auth"])
    application.include_router(admin_salon.router, prefix="/api/admin/salon", tags=["admin-salon"])
    application.include_router(admin_services.router, prefix="/api/admin/services", tags=["admin-services"])
    application.include_router(admin_schedule.router, prefix="/api/admin/schedule", tags=["admin-schedule"])
    application.include_router(admin_bookings.router, prefix="/api/admin/bookings", tags=["admin-bookings"])

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
