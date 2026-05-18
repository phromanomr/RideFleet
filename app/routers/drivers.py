from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import DriverRequest, DriverResponse
from app.services.driver_service import (
    criar_motorista,
    listar_motoristas,
    buscar_motorista,
    atualizar_disponibilidade,
    deletar_motorista
)

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.post("/", response_model=DriverResponse, status_code=201)
async def create_driver(body: DriverRequest, db: AsyncSession = Depends(get_db)):
    motorista = await criar_motorista(body.name, body.license_plate, db)
    return motorista

@router.get("/{driver_id}", response_model=DriverResponse, status_code=200)
async def get_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    motorista = await buscar_motorista(driver_id, db)
    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    return motorista

@router.patch("/{driver_id}/availability", response_model=DriverResponse, status_code=200)
async def update_availability(driver_id: str, available: bool, db: AsyncSession = Depends(get_db)):
    motorista = await atualizar_disponibilidade(driver_id, available, db)
    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
    return motorista

@router.delete("/{driver_id}", status_code=204)
async def delete_driver(driver_id: str, db: AsyncSession = Depends(get_db)):
    deletado = await deletar_motorista(driver_id, db)
    if not deletado:
        raise HTTPException(status_code=404, detail="Motorista não encontrado")
