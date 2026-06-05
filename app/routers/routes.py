from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os

router = APIRouter(prefix="/routes", tags=["routes"])

ORS_API_KEY = os.getenv("ORS_API_KEY")


class Coordinate(BaseModel):
    lat: float
    lng: float


class RouteRequest(BaseModel):
    origin: Coordinate
    destination: Coordinate


@router.post("/")
def calculate_route(data: RouteRequest):

    response = requests.post(
        "https://api.openrouteservice.org/v2/directions/driving-car/geojson",
        headers={
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "coordinates": [
                [data.origin.lng, data.origin.lat],
                [data.destination.lng, data.destination.lat],
            ]
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )

    result = response.json()

    if not result.get("features"):
        raise HTTPException(
            status_code=404,
            detail="Nenhuma rota encontrada",
        )

    feature = result["features"][0]

    route_coordinates = feature["geometry"]["coordinates"]

    leaflet_route = [
        [lat, lng]
        for lng, lat in route_coordinates
    ]

    summary = feature["properties"]["summary"]

    distance_meters = summary["distance"]
    duration_seconds = summary["duration"]

    return {
        "distanceKm": round(distance_meters / 1000, 2),
        "durationMin": round(duration_seconds / 60, 1),
        "route": leaflet_route,
    }