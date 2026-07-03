from pydantic import BaseModel, Field, field_validator

class Location(BaseModel):
    lat: float
    lng: float
    street: str | None = ""
    number: str | None = ""
    city: str | None = ""
    state: str | None = ""

    @field_validator("street", "number", "city", "state", mode="before")
    @classmethod
    def null_para_vazio(cls, value):
        return "" if value is None else value

class GeoLocation(BaseModel):
    lat: float
    lng: float

class Address(BaseModel):
    endereco: str = Field(..., description="Endereço completo para buscar (ex: Rua X, 123, Cidade, Estado)")
