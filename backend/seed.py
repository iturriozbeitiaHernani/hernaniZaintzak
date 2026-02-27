"""
Script para inicializar la base de datos con datos mínimos.
Ejecutar una sola vez tras `alembic upgrade head`:

    cd backend
    python seed.py
"""
import asyncio

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.center_config import CenterConfig
from app.models.user import User


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Usuario administrador
        admin = User(
            email="admin@centro.es",
            hashed_password=hash_password("admin123"),
            nombre="Administrador",
            rol="admin",
        )
        db.add(admin)

        # Configuración del centro (valores por defecto)
        config = CenterConfig(id=1)
        db.add(config)

        await db.commit()
        print("✓ Seed completado")
        print("  Email: admin@centro.es")
        print("  Password: admin123")
        print("  Cambia la contraseña en producción.")


if __name__ == "__main__":
    asyncio.run(seed())
