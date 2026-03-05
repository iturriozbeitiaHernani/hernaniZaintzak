"""Script de prueba: registra ausencia y espera las sustituciones generadas por IA."""
import asyncio
import json
import time

import httpx

BASE = "http://localhost:8000"


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE, timeout=120) as client:
        # Login
        r = await client.post("/api/auth/login", json={"email": "admin@centro.es", "password": "admin123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login OK")

        # Registrar ausencia de Josu (ID=2) el lunes 2026-03-02
        r2 = await client.post("/api/absences", headers=headers, json={
            "teacher_id": 2,
            "fecha_inicio": "2026-03-02",
            "fecha_fin": "2026-03-02",
            "motivo": "Enfermedad",
            "descripcion": "Ausencia de prueba - gripe",
        })
        if r2.status_code == 409:
            print("409: Ya existe ausencia para ese periodo — prueba con otro profesor o fecha")
            return
        print(f"Ausencia creada (status {r2.status_code}):")
        print(json.dumps(r2.json(), indent=2, ensure_ascii=False))
        absence_id = r2.json()["id"]

        # Esperar a que la IA procese en background
        print("\nEsperando 40s a que Claude genere las propuestas...")
        for i in range(4):
            await asyncio.sleep(10)
            print(f"  {(i+1)*10}s ...")

        # Ver sustituciones generadas
        r3 = await client.get("/api/substitutions", headers=headers)
        subs = r3.json()
        print(f"\n=== Sustituciones totales en DB: {len(subs)} ===")
        for s in subs:
            print(json.dumps(s, indent=2, ensure_ascii=False))

        # Ver ausencia actualizada
        r4 = await client.get(f"/api/absences/{absence_id}", headers=headers)
        print(f"\n=== Ausencia {absence_id} (estado actualizado) ===")
        print(json.dumps(r4.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
