from pydantic import BaseModel, Field

class Location(BaseModel):
    lat: float
    lng: float
    street: str | None = None
    number: str | None = None
    city: str | None = None
    state: str | None = None

class GeoLocation(BaseModel):
    lat: float
    lng: float

class Address(BaseModel):
    endereco: str = Field(..., description="Endereço completo para buscar (ex: Rua X, 123, Cidade, Estado)")
