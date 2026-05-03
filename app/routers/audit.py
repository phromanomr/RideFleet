from fastapi import APIRouter
from app.distributed.logical_clock import get_audit_log

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/rides/{ride_id}")
async def get_ride(ride_id: str):
    events = get_audit_log(ride_id)
    return {
        "ride_id": ride_id,
        "total_events": len(events),
        "events": events
    }