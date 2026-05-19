import uuid
from typing import Any, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.driver_model import DriverModel

async def criar_motorista(name: str, licence_plate: str, db: AsyncSession) -> DriverModel | None:
    motorista = DriverModel(
        id=str(uuid.uuid4()),
        name=name,
        license_plate=licence_plate,
        available=True
    )
    db.add(motorista)
    await db.commit()
    await db.refresh(motorista)
    return motorista

async def listar_motoristas(db: AsyncSession) -> Sequence[Any]:
    result = await db.execute(select(DriverModel))
    return result.scalars().all()

async def buscar_motorista(driver_id: str, db: AsyncSession) -> DriverModel | None:
    result = await db.execute(
        select(DriverModel).where(DriverModel.id == driver_id)
    )
    return result.scalar_one_or_none()

async def atualizar_disponibilidade(driver_id: str, available:bool, db: AsyncSession) -> DriverModel | None:
    motorista = await buscar_motorista(driver_id, db)
    if not motorista:
        return None
    motorista.available = available
    await db.commit()
    await db.refresh(motorista)
    return motorista

async def deletar_motorista(driver_id: str, db: AsyncSession) -> bool:
    motorista = await buscar_motorista(driver_id, db)
    if not motorista:
        return False
    await db.delete(motorista)
    await db.commit()
    return True

async def contar_motoristas(db: AsyncSession) -> dict:
    motoristas = await listar_motoristas(db)
    total = len(motoristas)
    disponiveis = sum(1 for m in motoristas if m.available)
    return {
        "total": total,
        "available": disponiveis,
        "busy": total - disponiveis
    }
