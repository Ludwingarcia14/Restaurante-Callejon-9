from flask import jsonify, session
from datetime import datetime, timedelta
from config.db import db
from bson import ObjectId

class PropinasController:

    @staticmethod
    def propinas_hoy():
        """Obtiene las propinas del mesero del día actual"""
        mesero_id = session.get("usuario_id")
        
        if not mesero_id:
            return jsonify({"success": False, "error": "Sesión no válida"}), 401
        
        try:
            mesero_oid = ObjectId(mesero_id)
            
            # 🔥 USAR HORA LOCAL (NO UTC)
            inicio_dia = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            fin_dia = inicio_dia + timedelta(days=1)
            
            print(f"\n{'='*60}")
            print(f"💵 PROPINAS DEL DÍA - DEBUG")
            print(f"{'='*60}")
            print(f"Mesero ID: {mesero_id}")
            print(f"Inicio día: {inicio_dia}")
            print(f"Fin día: {fin_dia}")
            
            # 🔥 Obtener propinas del día
            propinas = list(db.propinas.find({
                "mesero_id": mesero_oid,
                "fecha": {
                    "$gte": inicio_dia,
                    "$lt": fin_dia
                }
            }).sort("fecha", -1))
            
            print(f"📊 Propinas encontradas: {len(propinas)}")
            
            # Calcular total
            total_propinas = sum(float(p.get("monto", 0)) for p in propinas)
            
            print(f"💰 Total de propinas: ${total_propinas:.2f}")
            
            # Formatear para el frontend
            propinas_formateadas = []
            for p in propinas:
                propinas_formateadas.append({
                    "id": str(p["_id"]),
                    "monto": float(p.get("monto", 0)),
                    "porcentaje": float(p.get("porcentaje", 0)),
                    "mesa": p.get("mesa_numero"),
                    "metodo_pago": p.get("metodo_pago", "efectivo"),
                    "fecha": p.get("fecha").isoformat() if p.get("fecha") else None
                })
                print(f"   ✅ Mesa {p.get('mesa_numero')}: ${p.get('monto', 0):.2f} ({p.get('metodo_pago', 'efectivo')})")
            
            print(f"{'='*60}\n")
            
            return jsonify({
                "success": True,
                "total": total_propinas,
                "propinas": propinas_formateadas,
                "count": len(propinas_formateadas)
            })
            
        except Exception as e:
            print(f"❌ Error al obtener propinas: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500