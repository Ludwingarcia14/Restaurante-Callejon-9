from config.db import db
from datetime import datetime
from bson.objectid import ObjectId

class Financiera:
    collection = db["financieras"]

    def __init__(self, financiera_nombre=None, financiera_nombreAliado=None, financiera_correo=None,
                 financiera_direccioncorreo=None, financiera_NContrato=None, financiera_prestamoOfrecido=None,
                 financiera_cobertura=None, financiera_montoFinanciacion=None, financiera_TiempoR_M_M=None,
                 financiera_DepositosMinimos=None, financiera_SaldosPromediosM=None, financiera_TasaInteres=None,
                 financiera_ClaveCIEC=None, financiera_Plazos=None, financiera_CobroComisionA=None,
                 financiera_GarantiaMoviliaria=None, financiera_PropuestaValor=None, financiera_PorcentajeComision=None,
                 financiera_presentacionLink=None, financiera_perfilsolicitante=None, financiera_antiguedad=None,
                 financiera_edadM=None, financiera_nivelventas=None, financiera_historialcrediticio=None,
                 financiera_scoreminimoburo=None, financiera_estadosfinancieros=None, financiera_mopermitido=None,
                 financiera_girosrestringidos=None, financiera_girospreferidos=None, financiera_porcentajeminimoa=None,
                 financiera_antiguedadminimacambio=None, financiera_concentracioningresos=None,
                 financiera_porcentajeventasgobierno=None, financiera_informacionadicionalcliente=None,
                 financiera_checklistsolicitante=None, created_at=None, updated_at=None, _id=None):

        self._id = _id
        self.financiera_nombre = financiera_nombre
        self.financiera_nombreAliado = financiera_nombreAliado
        self.financiera_correo = financiera_correo
        self.financiera_direccioncorreo = financiera_direccioncorreo
        self.financiera_NContrato = financiera_NContrato
        self.financiera_prestamoOfrecido = financiera_prestamoOfrecido
        self.financiera_cobertura = financiera_cobertura
        self.financiera_montoFinanciacion = financiera_montoFinanciacion
        self.financiera_TiempoR_M_M = financiera_TiempoR_M_M
        self.financiera_DepositosMinimos = financiera_DepositosMinimos
        self.financiera_SaldosPromediosM = financiera_SaldosPromediosM
        self.financiera_TasaInteres = financiera_TasaInteres
        self.financiera_ClaveCIEC = financiera_ClaveCIEC
        self.financiera_Plazos = financiera_Plazos
        self.financiera_CobroComisionA = financiera_CobroComisionA
        self.financiera_GarantiaMoviliaria = financiera_GarantiaMoviliaria
        self.financiera_PropuestaValor = financiera_PropuestaValor
        self.financiera_PorcentajeComision = financiera_PorcentajeComision
        self.financiera_presentacionLink = financiera_presentacionLink
        self.financiera_perfilsolicitante = financiera_perfilsolicitante
        self.financiera_antiguedad = financiera_antiguedad
        self.financiera_edadM = financiera_edadM
        self.financiera_nivelventas = financiera_nivelventas
        self.financiera_historialcrediticio = financiera_historialcrediticio
        self.financiera_scoreminimoburo = financiera_scoreminimoburo
        self.financiera_estadosfinancieros = financiera_estadosfinancieros
        self.financiera_mopermitido = financiera_mopermitido
        self.financiera_girosrestringidos = financiera_girosrestringidos
        self.financiera_girospreferidos = financiera_girospreferidos
        self.financiera_porcentajeminimoa = financiera_porcentajeminimoa
        self.financiera_antiguedadminimacambio = financiera_antiguedadminimacambio
        self.financiera_concentracioningresos = financiera_concentracioningresos
        self.financiera_porcentajeventasgobierno = financiera_porcentajeventasgobierno
        self.financiera_informacionadicionalcliente = financiera_informacionadicionalcliente
        self.financiera_checklistsolicitante = financiera_checklistsolicitante
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    # 📌 Convierte el objeto en un diccionario (para insertar/actualizar en MongoDB)
    def to_dict(self):
        return {
            "financiera_nombre": self.financiera_nombre,
            "financiera_nombreAliado": self.financiera_nombreAliado,
            "financiera_correo": self.financiera_correo,
            "financiera_direccioncorreo": self.financiera_direccioncorreo,
            "financiera_NContrato": self.financiera_NContrato,
            "financiera_prestamoOfrecido": self.financiera_prestamoOfrecido,
            "financiera_cobertura": self.financiera_cobertura,
            "financiera_montoFinanciacion": self.financiera_montoFinanciacion,
            "financiera_TiempoR_M_M": self.financiera_TiempoR_M_M,
            "financiera_DepositosMinimos": self.financiera_DepositosMinimos,
            "financiera_SaldosPromediosM": self.financiera_SaldosPromediosM,
            "financiera_TasaInteres": self.financiera_TasaInteres,
            "financiera_ClaveCIEC": self.financiera_ClaveCIEC,
            "financiera_Plazos": self.financiera_Plazos,
            "financiera_CobroComisionA": self.financiera_CobroComisionA,
            "financiera_GarantiaMoviliaria": self.financiera_GarantiaMoviliaria,
            "financiera_PropuestaValor": self.financiera_PropuestaValor,
            "financiera_PorcentajeComision": self.financiera_PorcentajeComision,
            "financiera_presentacionLink": self.financiera_presentacionLink,
            "financiera_perfilsolicitante": self.financiera_perfilsolicitante,
            "financiera_antiguedad": self.financiera_antiguedad,
            "financiera_edadM": self.financiera_edadM,
            "financiera_nivelventas": self.financiera_nivelventas,
            "financiera_historialcrediticio": self.financiera_historialcrediticio,
            "financiera_scoreminimoburo": self.financiera_scoreminimoburo,
            "financiera_estadosfinancieros": self.financiera_estadosfinancieros,
            "financiera_mopermitido": self.financiera_mopermitido,
            "financiera_girosrestringidos": self.financiera_girosrestringidos,
            "financiera_girospreferidos": self.financiera_girospreferidos,
            "financiera_porcentajeminimoa": self.financiera_porcentajeminimoa,
            "financiera_antiguedadminimacambio": self.financiera_antiguedadminimacambio,
            "financiera_concentracioningresos": self.financiera_concentracioningresos,
            "financiera_porcentajeventasgobierno": self.financiera_porcentajeventasgobierno,
            "financiera_informacionadicionalcliente": self.financiera_informacionadicionalcliente,
            "financiera_checklistsolicitante": self.financiera_checklistsolicitante,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    # --- Métodos CRUD ---
    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})

    @classmethod
    def create(cls, data):
        data["created_at"] = datetime.utcnow()
        data["updated_at"] = datetime.utcnow()
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, id, data):
        data["updated_at"] = datetime.utcnow()
        return cls.collection.update_one({"_id": ObjectId(id)}, {"$set": data})

    @classmethod
    def delete(cls, id):
        return cls.collection.delete_one({"_id": ObjectId(id)})

    @classmethod
    def get_all(cls, limit=None):
        cursor = cls.collection.find()
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)


    @staticmethod
    def view_prestamo_crear():
        """Muestra el formulario para crear un nuevo préstamo"""
        if "usuario_id" not in session:
            return redirect(url_for("routes.login2"))
        
        # Obtenemos la lista de clientes para poder seleccionar uno
        financiera_id = session.get("usuario_id")
        clientes = list(db.clientes.find({"cliente_idFinanciera": financiera_id}))
        
        return render_template(
            "financieras/gestion_prestamo/crear_prestamo.html",
            clientes=clientes,
            usuario=session.get("usuario_nombre")
        )

    @staticmethod
    def store_prestamo():
        """Guarda el nuevo préstamo en la BD"""
        if "usuario_id" not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401

        data = request.form
        financiera_id = session.get("usuario_id")

        try:
            # Buscar nombre del cliente para guardarlo desnormalizado (opcional, ayuda al rendimiento)
            cliente = db.clientes.find_one({"_id": ObjectId(data.get("cliente_id"))})
            cliente_nombre = f"{cliente.get('cliente_nombre')} {cliente.get('cliente_apellidos')}" if cliente else "Desconocido"

            nuevo_prestamo = {
                "financiera_id": financiera_id,
                "cliente_id": data.get("cliente_id"),
                "cliente_nombre": cliente_nombre, # Guardamos el nombre para facilitar la tabla
                "folio_prestamo": data.get("folio") or str(uuid.uuid4())[:8].upper(),
                "prestamo_monto": float(data.get("monto")),
                "prestamo_tasa_interes": float(data.get("tasa")),
                "prestamo_estado": "Activo",
                "fecha_inicio": data.get("fecha_inicio"),
                "fecha_vencimiento": data.get("fecha_vencimiento"),
                "observaciones": data.get("observaciones"),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            db.prestamos.insert_one(nuevo_prestamo)
            
            return jsonify({"status": "success", "message": "Préstamo creado correctamente"})
        except Exception as e:
            print(f"Error store prestamo: {e}")
            return jsonify({"status": "error", "message": "Error al guardar"})