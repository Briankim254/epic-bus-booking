from fastapi import APIRouter

from app.api.routes import (
    admin_buses,
    admin_trips,
    bookings,
    fares,
    health,
    towns,
    trips,
)

api_router = APIRouter()
for module in (health, towns, fares, trips, bookings, admin_trips, admin_buses):
    api_router.include_router(module.router)
