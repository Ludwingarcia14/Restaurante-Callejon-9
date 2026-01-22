import bcrypt, secrets, uuid, logging
from datetime import datetime
from bson import ObjectId
# Importaciones relativas dentro del módulo CQRS
from ..models.register_client_command import RegisterClientCommand
# Importación del servicio compartido
from cqrs.commands.services.recaptcha_service import RecaptchaService

class RegisterClientCommandHandler:
    @staticmethod
    # 1. ACEPTAR EL NUEVO PARÁMETRO asesor_id
    def handle(command: RegisterClientCommand, db_accessor, client_model, asesor_id):

        errors = []

        # 1. Validación de reCAPTCHA (delegada al servicio)
        RecaptchaService.verify(command.recaptcha_response, command.remote_addr, errors)

        # 2. Validaciones básicas de datos
        if not all([command.nombre, command.apellidos, command.email, command.fecha_nac, command.password, command.password_confirm]):
            errors.append("Faltan campos obligatorios.")

        if command.password != command.password_confirm:
            errors.append("Las contraseñas no coinciden.")

        # Validación de unicidad de email (Consulta directa)
        if db_accessor.clientes.find_one({"cliente_email": command.email}):
            errors.append("El correo electrónico ya está registrado.")

        try:
            fecha_nac_dt = datetime.strptime(command.fecha_nac, '%Y-%m-%d')
        except ValueError:
            errors.append("El formato de fecha de nacimiento es incorrecto. Debe ser YYYY-MM-DD.")

        if errors:
            raise ValueError(errors[0]) # Lanza el error para ser capturado por el controlador

        # 3. Hashing de Contraseña
        salt = bcrypt.gensalt(rounds=12)
        hashed_password = bcrypt.hashpw(command.password.encode("utf-8"), salt).decode("utf-8")

        # 4. Preparar y Persistir Datos (Escritura 1)
        # 4a. Definir el ID del asesor a usar (si está presente y es válido)
        final_asesor_id = None

        # ------------------------------------------------------------------
        # 2. LÓGICA DE PRIORIDAD DE ASIGNACIÓN (Paso preliminar)
        # ------------------------------------------------------------------
        if asesor_id:
            # Intentar validar si el ID proporcionado es un ObjectId válido de la BD
            try:
                # 💡 IMPORTANTE: Si el asesor_id viene del Front, puede ser un string. 
                # Debes intentar convertirlo a ObjectId si tu campo 'asesor_id' en la BD es ObjectId.
                asesor_obj_id = ObjectId(asesor_id)

                # Opcional: Verificar que el asesor realmente exista y esté activo
                asesor_existente = db_accessor.usuarios.find_one({
                    "_id": asesor_obj_id,
                    "usuario_rol": "3",
                    "usuario_tipo_asesor": "interno" # O el tipo que maneja referencias externas
                })

                if asesor_existente:
                    final_asesor_id = asesor_obj_id
                    logging.info(f"Asesoría asignada por referencia: {asesor_id}")
                else:
                    logging.warning(f"Asesor ID {asesor_id} no es válido o no existe. Recurriendo al balanceo.")

            except Exception as e:
                logging.error(f"Error al procesar asesor_id {asesor_id}: {e}")


        # 4b. Preparar datos base del cliente
        nuevo_cliente_data = {
            "cliente_idUsuario": str(uuid.uuid4()),
            "cliente_idFinanciera": 0,
            "cliente_nombre": command.nombre,
            "cliente_apellidos": command.apellidos,
            "cliente_email": command.email,
            "cliente_telefono": command.telefono if command.telefono else None,
            "cliente_fechaN": fecha_nac_dt,
            "cliente_clave": hashed_password,
            "cliente_rol": 4,
            "cliente_status": 0,
            "cliente_status_revision": 1,
            "cliente_token": secrets.token_urlsafe(32),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        resultado = db_accessor.clientes.insert_one(nuevo_cliente_data)
        nuevo_cliente_id = resultado.inserted_id

        # 5. Asignación de Asesor
        try:
            # ------------------------------------------------------------------
            # 3. MODIFICACIÓN DE ASIGNACIÓN: Usar el ID prioritario si existe
            # ------------------------------------------------------------------
            if final_asesor_id:
                # Usar el ID capturado de la URL
                asesor_pyme_id = final_asesor_id
            else:
                # Si no hay ID válido, ejecutar la lógica de balanceo
                asesor_pyme = RegisterClientCommandHandler._find_next_balanced_asesor(db_accessor)
                asesor_pyme_id = asesor_pyme['_id'] if asesor_pyme else None

            if asesor_pyme_id:
                # Crear la asignación
                db_accessor.asesor_asignado.insert_one({
                    "cliente_id": nuevo_cliente_id,
                    "asesor_id": asesor_pyme_id,
                    "created_at": datetime.utcnow()
                })
                # Actualizar el cliente con el asesor
                db_accessor.clientes.update_one(
                    {"_id": nuevo_cliente_id},
                    {"$set": {"cliente_idAsesor": asesor_pyme_id, "cliente_status": "en_revision_pyme"}}
                )
            else:
                logging.warning(f"No se pudo asignar asesor para el cliente {nuevo_cliente_id}. Queda pendiente.")

        except Exception as e:
            logging.error(f"Error al asignar asesor (No fatal): {e}") 

        return {"success": True, "cliente_id": str(nuevo_cliente_id)}

    @staticmethod
    def _find_next_balanced_asesor(db_accessor):
        """Pipeline de agregación para encontrar al asesor con menos clientes."""
        pipeline = [
            {"$match": {"usuario_rol": "3", "usuario_tipo_asesor": "interno"}},
            {"$lookup": {"from": "asesor_asignado", "localField": "_id", "foreignField": "asesor_id", "as": "clientes_asignados"}},
            {"$addFields": {"conteo_clientes": { "$size": "$clientes_asignados" }}},
            {"$sort": { "conteo_clientes": 1 }},
            {"$limit": 1}
        ]
        resultado_agg = list(db_accessor.usuarios.aggregate(pipeline))
        return resultado_agg[0] if resultado_agg else None