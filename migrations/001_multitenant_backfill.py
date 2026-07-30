"""
Migracion 001 - Backfill de multi-tenancy.

Crea el restaurante (tenant) por defecto y asigna `tenant_id` a los documentos
existentes que aun no lo tienen. Es ADITIVO e IDEMPOTENTE: re-ejecutar no
duplica nada y solo toca documentos sin tenant_id.

Uso (desde la raiz del proyecto):
  python migrations/001_multitenant_backfill.py           # reporte (no escribe)
  python migrations/001_multitenant_backfill.py --apply   # aplica los cambios
"""
import sys

from config.db import db
from models.restaurante_model import Restaurante

# Colecciones con datos de negocio que pertenecen a un restaurante (tenant).
# Se excluyen: restaurantes (registro de tenants), users (coleccion legacy),
# configuracion/configuracion_sistema (singletons globales; se decidiran aparte),
# payment_sessions / "pedidos/comandas" (transitorias/legacy).
TENANT_COLLECTIONS = [
    "usuarios", "ventas", "cuentas", "cortes_caja", "comandas", "mesas",
    "insumos", "movimientos_inventario", "proveedores", "alertas_stock",
    "inventario", "platillos", "productos", "menu", "clientes", "propinas",
    "notificaciones", "actividad_reciente", "insights", "estadisticas_diarias",
    "tickets", "payment_preferences", "pedidos_movil", "pagos_movil",
    "delivery_orders",
]


def main(apply):
    existing = Restaurante.find_default()
    if apply:
        # tenant_id se guarda como STRING (consistente con sesion y JWT).
        default_id = str(Restaurante.ensure_default())
    else:
        default_id = str(existing["_id"]) if existing else "(se creara al aplicar)"
    print(f"Modo: {'APLICAR' if apply else 'REPORTE (dry-run)'}")
    print(f"Tenant por defecto: {default_id} {'' if existing else '[NUEVO]'}\n")

    # Documentos "sin tenant": ausente, null o cadena vacia. Se incluyen los dos
    # ultimos porque documentos creados en runtime antes de la correccion del
    # tenant quedaron con tenant_id="" (existe pero vacio) y el filtro original
    # por $exists no los alcanzaba.
    SIN_TENANT = {"$or": [
        {"tenant_id": {"$exists": False}},
        {"tenant_id": None},
        {"tenant_id": ""},
    ]}

    total = 0
    for col in TENANT_COLLECTIONS:
        faltan = db[col].count_documents(SIN_TENANT)
        if apply and faltan:
            db[col].update_many(SIN_TENANT, {"$set": {"tenant_id": default_id}})
        total += faltan
        etiqueta = "asignados" if apply else "pendientes"
        marca = "" if faltan == 0 else "  <--"
        print(f"  {col:24} {etiqueta}={faltan}{marca}")

    print(f"\nTOTAL {'asignados' if apply else 'a asignar'}: {total}")


if __name__ == "__main__":
    main("--apply" in sys.argv)
