from pydantic import BaseModel

class Location(BaseModel):
    lat: float
    lng: float
    street: str
    number: str
    city: str
    state: str