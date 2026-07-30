"""
Migracion 002 — Unificar tenant.

El renombre del restaurante original ("Callejon 9" -> "Callejon 19") hizo que
Restaurante.ensure_default() (que buscaba por nombre) creara un segundo tenant
el 2026-07-30. Los clientes y pedidos nuevos quedaron en ese tenant fantasma,
mientras empleados/catalogo/inventario siguen en el original — por eso los
repartidores no veian los pedidos disponibles.

Esta migracion mueve los documentos del tenant fantasma al oficial y elimina
el restaurante fantasma. El fix de raiz esta en models/restaurante_model.py
(find_default ahora resuelve por slug, no por nombre editable).

Uso:
    python migrations/002_unificar_tenant.py           # dry-run (solo muestra)
    python migrations/002_unificar_tenant.py --apply   # aplica los cambios
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bson.objectid import ObjectId
from config.db import db

TENANT_OFICIAL = "6a41e77f0b68089f58c22143"   # restaurante original (2026-06-29)
TENANT_FANTASMA = "6a6b97493ab24483c8871b39"  # creado por accidente 2026-07-30

COLECCIONES = ["clientes", "pedidos_movil", "delivery_orders"]


def run(apply: bool):
    oficial = db["restaurantes"].find_one({"_id": ObjectId(TENANT_OFICIAL)})
    fantasma = db["restaurantes"].find_one({"_id": ObjectId(TENANT_FANTASMA)})
    if not oficial:
        print(f"ABORTADO: no existe el restaurante oficial {TENANT_OFICIAL}")
        return
    print(f"Oficial : {TENANT_OFICIAL} — {oficial.get('nombre')}")
    print(f"Fantasma: {TENANT_FANTASMA} — {fantasma.get('nombre') if fantasma else '(ya eliminado)'}")
    print(f"Modo    : {'APLICAR' if apply else 'DRY-RUN (sin cambios)'}\n")

    total = 0
    for col in COLECCIONES:
        n = db[col].count_documents({"tenant_id": TENANT_FANTASMA})
        total += n
        print(f"  {col}: {n} documentos a migrar")
        if apply and n:
            res = db[col].update_many(
                {"tenant_id": TENANT_FANTASMA},
                {"$set": {"tenant_id": TENANT_OFICIAL}},
            )
            print(f"    -> migrados: {res.modified_count}")

    if fantasma:
        print(f"\n  restaurantes: eliminar documento fantasma {TENANT_FANTASMA}")
        if apply:
            db["restaurantes"].delete_one({"_id": ObjectId(TENANT_FANTASMA)})
            print("    -> eliminado")

    print(f"\nTOTAL {'migrados' if apply else 'a migrar'}: {total}")
    if not apply:
        print("Ejecuta con --apply para aplicar los cambios.")


if __name__ == "__main__":
    run(apply="--apply" in sys.argv)
