from fastapi import APIRouter

from app.services.fetch_flight import fetch_gate

router = APIRouter(
    prefix="/flights",
    tags=["flights"],
)


@router.get("/{flight_number}/gate")
async def get_suggested_gate_for_flight_number(flight_number: str):
    gate = await fetch_gate(flight_number=flight_number)

    return {"gate": gate}
