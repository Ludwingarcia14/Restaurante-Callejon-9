# Roles de usuario
ROL_ADMIN = "1"
ROL_MESERO = "2"
ROL_COCINA = "3"
ROL_INVENTARIO = "4"

ROLES_NOMBRES = {
    ROL_ADMIN: "Administrador",
    ROL_MESERO: "Mesero",
    ROL_COCINA: "Cocina",
    ROL_INVENTARIO: "Inventario",
}

# Estados de mesa
MESA_DISPONIBLE = "disponible"
MESA_OCUPADA = "ocupada"
MESA_RESERVADA = "reservada"
MESA_LIMPIEZA = "limpieza"

# Estados de comanda
COMANDA_PENDIENTE = "pendiente"
COMANDA_ENVIADA = "enviada"
COMANDA_EN_PREPARACION = "en_preparacion"
COMANDA_LISTA = "lista"
COMANDA_ENTREGADA = "entregada"
COMANDA_PAGADA = "pagada"
COMANDA_CERRADA = "cerrada"

# Estados de venta
VENTA_PENDIENTE = "pendiente"
VENTA_COMPLETADA = "completada"
VENTA_CANCELADA = "cancelada"

# Métodos de pago
PAGO_EFECTIVO = "efectivo"
PAGO_TARJETA = "tarjeta"
PAGO_TRANSFERENCIA = "transferencia"
PAGO_MIXTO = "mixto"

# Configuración
SESION_TTL_SEGUNDOS = 86400  # 24 horas
TASA_IMPUESTO = 0.16         # 16% IVA
UMBRAL_STOCK_BAJO = 1.5      # factor sobre mínimo
