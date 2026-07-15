from models.venta_model import Venta, CorteCaja
from datetime import datetime


class VentaService:

    @staticmethod
    def calcular_stats_ventas(ventas: list) -> dict:
        stats = {
            "total_ventas": 0.0,
            "num_transacciones": len(ventas),
            "efectivo": 0.0,
            "tarjeta": 0.0,
            "transferencia": 0.0,
            "propinas": 0.0
        }
        for venta in ventas:
            total = float(venta.get("total", 0))
            stats["total_ventas"] += total
            stats["propinas"] += float(venta.get("propina", 0))
            metodo = venta.get("metodo_pago", "efectivo")
            if metodo in stats:
                stats[metodo] += total
        return stats

    @staticmethod
    def generar_corte(usuario_id: str, usuario_nombre: str, notas: str = "") -> str:
        ventas_hoy = Venta.find_hoy()
        stats = VentaService.calcular_stats_ventas(ventas_hoy)
        data = {
            "usuario_id": usuario_id,
            "usuario_nombre": usuario_nombre,
            "fecha_inicio": datetime.now().replace(hour=0, minute=0, second=0),
            "fecha_fin": datetime.utcnow(),
            "ventas": [str(v.get("_id")) for v in ventas_hoy],
            "total_ventas": stats["total_ventas"],
            "total_efectivo": stats["efectivo"],
            "total_tarjeta": stats["tarjeta"],
            "total_transferencia": stats["transferencia"],
            "total_propinas": stats["propinas"],
            "num_transacciones": stats["num_transacciones"],
            "notas": notas
        }
        return CorteCaja.create(data)
