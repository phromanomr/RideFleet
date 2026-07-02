from pydantic import BaseModel, Field

class Location(BaseModel):
    lat: float
    lng: float
    street: str | None = ""
    number: str | None = ""
    city: str | None = ""
    state: str | None = ""

class GeoLocation(BaseModel):
    lat: float
    lng: float

class Address(BaseModel):
    endereco: str = Field(..., description="Endereço completo para buscar (ex: Rua X, 123, Cidade, Estado)")
