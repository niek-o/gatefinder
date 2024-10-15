from fastapi import APIRouter

from app.services.fetch_flight import fetch_flight

router = APIRouter(
    prefix="/flights",
    tags=["flights"],
)


@router.get("/{flight_number}/gate")
async def get_suggested_gate_for_flight_number(flight_number: str):
    return await fetch_flight(flight_number=flight_number)
