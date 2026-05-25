from config.db import db
from bson import ObjectId
from datetime import datetime, timedelta


class PropinaService:

    @staticmethod
    def get_hoy(mesero_id: str) -> dict:
        inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(days=1)

        propinas = list(db.propinas.find({
            "mesero_id": ObjectId(mesero_id),
            "fecha": {"$gte": inicio, "$lt": fin}
        }).sort("fecha", -1))

        total = sum(float(p.get("monto", 0)) for p in propinas)
        formateadas = [{
            "id": str(p["_id"]),
            "monto": float(p.get("monto", 0)),
            "porcentaje": float(p.get("porcentaje", 0)),
            "mesa": p.get("mesa_numero"),
            "metodo_pago": p.get("metodo_pago", "efectivo"),
            "fecha": p.get("fecha").isoformat() if p.get("fecha") else None
        } for p in propinas]

        return {"total": total, "propinas": formateadas, "count": len(formateadas)}

    @staticmethod
    def calcular_rango(rango: str, mes: str = None) -> tuple:
        hoy = datetime.now()
        if rango == "dia":
            inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
            fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif rango == "semana":
            inicio = (hoy - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
            fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif rango == "mes" and mes:
            anio, mes_num = map(int, mes.split("-"))
            inicio = datetime(anio, mes_num, 1)
            fin = (datetime(anio + 1, 1, 1) if mes_num == 12 else datetime(anio, mes_num + 1, 1)) - timedelta(seconds=1)
        else:
            inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            fin = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        return inicio, fin

    @staticmethod
    def get_rango(mesero_id: str, rango: str, mes: str = None) -> dict:
        inicio, fin = PropinaService.calcular_rango(rango, mes)

        propinas = list(db.propinas.find({
            "mesero_id": ObjectId(mesero_id),
            "fecha": {"$gte": inicio, "$lte": fin}
        }))

        por_dia: dict = {}
        for p in propinas:
            dia = p["fecha"].strftime("%Y-%m-%d")
            por_dia[dia] = round(por_dia.get(dia, 0) + float(p.get("monto", 0)), 2)

        dias = []
        current = inicio
        while current.date() <= fin.date():
            fecha_str = current.strftime("%Y-%m-%d")
            dias.append({"fecha": fecha_str, "total": por_dia.get(fecha_str, 0)})
            current += timedelta(days=1)

        return {"dias": dias, "total": round(sum(por_dia.values()), 2), "rango": rango}
