# Registro de código obsoleto — Fase 2 (limpieza)

Este archivo registra el código que quedó obsoleto tras implementar el nuevo
flujo de delivery (cocina marca "listo" → repartidores aceptan → admin solo
monitorea). **Nada de esto se ha eliminado aún**: la limpieza se hará en una
fase 2, después de validar el flujo completo de extremo a extremo.

## Desactivado (código presente, sin ejecutarse)

| Ubicación | Qué es | Cómo quedó |
|---|---|---|
| `controllers/api/v1/pedido_movil_controller.py` — bloque delivery de `crear_pedido` | Creación del `DeliveryOrder` al momento del pedido | Detrás de la bandera `CREAR_DELIVERY_AL_CREAR_PEDIDO = False` (línea ~28). Eliminar bloque y bandera en fase 2. |

## Obsoleto pero aún activo (eliminar en fase 2)

| Ubicación | Qué es | Por qué queda obsoleto |
|---|---|---|
| `controllers/repartidor/repartidor_controller.py::DeliveryAPIController.asignar` + ruta `PUT /api/delivery/<id>/asignar` (`routes/repartidor_routes.py`) | Asignación manual de repartidor por el Admin | Reemplazado por `POST /api/delivery/<id>/aceptar` (auto-aceptación atómica del repartidor). |
| `models/delivery_model.py::DeliveryOrder.asignar_repartidor` | Update no atómico usado por `asignar` | Reemplazado por `aceptar_por_repartidor` (atómico). |
| `models/delivery_model.py` — campo `estado_cocina` + `set_estado_cocina` | Espejo del avance de cocina en la orden de entrega | El `DeliveryOrder` ahora nace cuando cocina marca "listo"; nunca existe en estado "cocina sin terminar". Nota: `_crear_delivery_al_marcar_listo` aún lo escribe (`"listo"`) para que el badge del panel admin actual siga siendo correcto — quitar ambos juntos. |
| `services/cocina_service.py::_sincronizar_delivery_con_cocina` + evento socket `delivery_cocina_actualizado` + sala `admins` | Sincronización cocina→delivery y aviso al admin "ya puedes asignar" | Sin sentido cuando la orden nace lista. El panel admin deberá escuchar otro evento (o refrescar por polling, que ya hace). |
| `controllers/api/v1/pedido_movil_controller.py::actualizar_estado` + ruta `PATCH /api/v1/admin/pedidos-movil/<id>/estado` (`routes_v1.py`) | Endpoint JWT duplicado para cambiar estado de cocina | Ya estaba muerto antes de este cambio (ningún frontend lo llama); no pasa por la creación del `DeliveryOrder`, dejaría pedidos delivery huérfanos. |
| `resources/views/admin/delivery_panel.html` — modal "Asignar Repartidor", botones Asignar/Reasignar, JS `abrirAsignar`/`confirmarAsignacion`, `join_room('admins')`, listener `delivery_cocina_actualizado`, toast "Ya puede asignarse un repartidor" | UI de asignación manual del admin | El admin pasa a solo monitoreo (el botón Cancelar sí se conserva). El toast actual dice "Ya puede asignarse un repartidor", que ya no es cierto. |
| `AdminDeliveryViewController.panel` — parámetro `repartidores` al template | Alimentaba el `<select>` del modal de asignación | Sin uso cuando se quite el modal. |
| `resources/views/repartidor/mis_entregas.html` — texto "El administrador te asignará pedidos pronto." | Copy del flujo viejo | Actualizar al copy del flujo nuevo (dashboard ya se actualizó). |
| `resources/views/mesero/dashboard.html:1395` — texto "El admin lo asignará a un repartidor." | Copy del flujo viejo en el dashboard del mesero | Actualizar copy. |

## Nuevo código agregado (referencia)

- `models/delivery_model.py`: `aceptar_por_repartidor`, `listar_disponibles`.
- `services/cocina_service.py`: `_crear_delivery_al_marcar_listo` (crea la orden
  al marcar "listo" y emite `nuevo_pedido_disponible` → `repartidores_global`).
- `controllers/repartidor/repartidor_controller.py`: `DeliveryAPIController.aceptar`,
  `listar_disponibles_api`; propagación de `entregado`/`cancelado` al
  `PedidoMovil` enlazado dentro de `actualizar_estado` (corrige el bug del
  pedido del cliente "activo para siempre").
- `routes/repartidor_routes.py`: `GET /api/delivery/disponibles`,
  `POST /api/delivery/<id>/aceptar` (rol 5).
- `resources/views/repartidor/dashboard.html`: sección "Pedidos disponibles" +
  listeners `nuevo_pedido_disponible` / `pedido_tomado`.
- Eventos Socket.IO nuevos: `nuevo_pedido_disponible`, `pedido_tomado`
  (ambos en sala `repartidores_global`, ya existente en `app.py`).
