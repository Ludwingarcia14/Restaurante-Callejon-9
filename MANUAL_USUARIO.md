# Manual de Usuario — Sistema de Gestión Restaurante Callejón 9

> **Versión:** 1.0  
> **Fecha:** Abril 2026  
> **Dirigido a:** Administradores, Meseros, Personal de Cocina y Encargados de Inventario

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Acceso al Sistema](#2-acceso-al-sistema)
3. [Autenticación de Dos Factores (2FA)](#3-autenticación-de-dos-factores-2fa)
4. [Módulo Administrador](#4-módulo-administrador)
5. [Módulo Mesero](#5-módulo-mesero)
6. [Módulo Cocina](#6-módulo-cocina)
7. [Módulo Inventario](#7-módulo-inventario)
8. [Configuración de Cuenta](#8-configuración-de-cuenta)
9. [Notificaciones](#9-notificaciones)
10. [Preguntas Frecuentes](#10-preguntas-frecuentes)

---

## 1. Introducción

El **Sistema de Gestión Restaurante Callejón 9** es una plataforma digital que centraliza las operaciones del restaurante en un solo lugar. Permite coordinar en tiempo real la atención de mesas, la preparación de pedidos en cocina, el control de inventario y el análisis de ventas.

### Roles del Sistema

| Rol | Función Principal |
|-----|------------------|
| **Administrador** | Gestiona empleados, menú, ventas, analytics y configuración general |
| **Mesero** | Atiende mesas, genera comandas, cobra y consulta su historial |
| **Cocina** | Recibe y procesa pedidos en tiempo real |
| **Inventario** | Controla insumos, registra movimientos y gestiona proveedores |

> Cada usuario accede únicamente a las secciones correspondientes a su rol. El sistema redirige automáticamente al panel correcto al iniciar sesión.

---

## 2. Acceso al Sistema

### 2.1 Inicio de Sesión

1. Abrir el navegador e ingresar la dirección del sistema (proporcionada por el administrador).
2. Ingresar el **correo electrónico** y la **contraseña** asignados.
3. Presionar el botón **Iniciar Sesión**.

![Pantalla de login]

> Si las credenciales son incorrectas, aparecerá un mensaje de error en rojo. Verificar que el correo esté escrito correctamente y que la contraseña no tenga espacios adicionales.

### 2.2 Redirección Automática por Rol

Una vez autenticado, el sistema redirige automáticamente al panel correspondiente:

| Rol | Ruta de acceso |
|-----|---------------|
| Administrador | `/dashboard/admin` |
| Mesero | `/dashboard/mesero` |
| Cocina | `/dashboard/cocina` |
| Inventario | `/inventario/dashboard` |

### 2.3 Cierre de Sesión

Para cerrar sesión de forma segura, hacer clic en el botón **Cerrar Sesión** ubicado en la parte inferior del menú lateral izquierdo. Esto limpia la sesión activa y regresa a la pantalla de inicio de sesión.

> **Recomendación:** Cerrar siempre la sesión al terminar el turno, especialmente en equipos compartidos.

---

## 3. Autenticación de Dos Factores (2FA)

La autenticación de dos factores agrega una capa adicional de seguridad a la cuenta. Una vez activada, el sistema solicitará un código de 6 dígitos en cada inicio de sesión, además de la contraseña.

### 3.1 Activar el 2FA

1. Iniciar sesión en el sistema.
2. En el menú lateral, hacer clic en **Configuración** (ícono de engranaje).
3. Seleccionar la pestaña **Seguridad**.
4. Elegir el método de verificación:
   - **App Autenticadora** (recomendado): Google Authenticator, Authy u otra aplicación TOTP.
   - **Correo Electrónico**: Se enviará un código al correo registrado.
5. Para el método **App**:
   - El sistema mostrará un código QR.
   - Abrir la aplicación autenticadora en el teléfono.
   - Escanear el código QR.
   - Ingresar el código de 6 dígitos que muestra la aplicación para confirmar.
6. Hacer clic en **Activar**. El 2FA quedará habilitado de inmediato.

### 3.2 Iniciar Sesión con 2FA Activo

1. Ingresar correo y contraseña normalmente.
2. Aparecerá una ventana solicitando el **código de verificación**.
3. Abrir la aplicación autenticadora en el teléfono y copiar el código de 6 dígitos.
4. Ingresar el código y presionar **Verificar**.
5. El sistema redirigirá al panel correspondiente.

> Los códigos TOTP cambian cada 30 segundos. Ingresar el código que muestra la aplicación en ese momento.

### 3.3 Desactivar el 2FA

1. Ir a **Configuración → Seguridad**.
2. Hacer clic en **Desactivar 2FA**.
3. Confirmar la acción.

### 3.4 Recuperación de Emergencia

Si se perdió acceso al dispositivo autenticador y no es posible iniciar sesión, comunicarse con el administrador del sistema para desactivar el 2FA mediante el procedimiento de emergencia.

---

## 4. Módulo Administrador

El administrador tiene acceso completo al sistema. Su panel principal muestra un resumen ejecutivo de las operaciones del restaurante.

### 4.1 Dashboard Principal

Al ingresar al panel de administrador se visualizan:

- **Estadísticas del día**: mesas ocupadas, ventas del turno, pedidos activos.
- **Personal activo**: empleados con sesión iniciada en ese momento.
- **Actividad reciente**: últimas acciones registradas en el sistema.
- **Notificaciones**: alertas de stock, logins y eventos importantes.

---

### 4.2 Gestión de Empleados

**Ruta:** Menú lateral → **Empleados**

#### Crear un Empleado

1. Hacer clic en **Nuevo Empleado**.
2. Completar el formulario:
   - Nombre y apellidos
   - Correo electrónico (será el usuario de acceso)
   - Contraseña temporal
   - Rol asignado (Mesero, Cocina, Inventario)
   - Campos específicos según el rol (número de empleado, turno, mesas asignadas, etc.)
3. Hacer clic en **Guardar**.

#### Editar un Empleado

1. Localizar al empleado en la lista.
2. Hacer clic en el ícono de **edición** (lápiz).
3. Modificar los campos necesarios.
4. Guardar los cambios.

#### Desactivar / Eliminar un Empleado

- **Desactivar:** Cambia el estado del empleado a inactivo sin borrar su historial.
- **Eliminar:** Borra permanentemente el registro. Esta acción no se puede deshacer.
- **Desconectar:** Cierra la sesión activa del empleado de forma remota.

> Al desactivar un empleado, éste no podrá iniciar sesión aunque tenga credenciales válidas.

---

### 4.3 Gestión del Menú

**Ruta:** Menú lateral → **Menú**

#### Agregar un Platillo

1. Hacer clic en **Nuevo Platillo**.
2. Completar:
   - Nombre del platillo
   - Descripción
   - Categoría (Entrada, Plato Fuerte, Bebida, Postre, Especial)
   - Precio de venta
   - Imagen (opcional)
   - Tiempo de preparación y dificultad
3. Guardar.

#### Activar o Desactivar un Platillo

Un platillo desactivado no aparece en el menú del mesero y no puede ser pedido. Esto es útil cuando un insumo no está disponible temporalmente.

1. Localizar el platillo en la lista.
2. Hacer clic en el botón de **activar/desactivar** (toggle).

#### Eliminar un Platillo

Hacer clic en el ícono de **papelera** y confirmar la eliminación. Esta acción es permanente.

---

### 4.4 Analytics y Reportes

**Ruta:** Menú lateral → **Analytics**

La sección de Analytics muestra métricas en tiempo real de los últimos 30 días generadas mediante consultas de agregación sobre MongoDB.

#### KPIs Generales

| KPI | Descripción |
|-----|-------------|
| Ventas Hoy | Total en pesos del día actual |
| Ventas Semana | Acumulado de los últimos 7 días |
| Ventas Mes | Acumulado de los últimos 30 días |
| Ticket Promedio | Promedio por venta en 30 días |
| Mesas Ocupadas | Mesas con cuenta abierta en este momento |

#### Gráficas Disponibles

- **Ventas Diarias:** Tendencia de ventas por día (línea).
- **Métodos de Pago:** Distribución entre efectivo, tarjeta, transferencia (dona).
- **Top 10 Platillos:** Los 10 platillos que generaron más ingresos (tabla con ranking).
- **Horas Pico:** Horas del día con mayor volumen de ventas (barras).
- **Rendimiento por Mesero:** Ventas totales y propinas por mesero (tabla).
- **Top 15 Mesas:** Mesas con mayor consumo acumulado (tabla).

Hacer clic en **Actualizar** (botón superior derecho) para refrescar todos los datos.

---

### 4.5 Gestión de Ventas

**Ruta:** Menú lateral → **Ventas**

Visualiza el historial completo de ventas con filtros por fecha, mesero y método de pago. Permite revisar el detalle de cada transacción.

---

### 4.6 Backup y Restauración

**Ruta:** Menú lateral → **Backup**

#### Crear un Respaldo

1. Hacer clic en **Crear Respaldo**.
2. El sistema genera un archivo `.json` con toda la información de la base de datos.
3. Descargar el archivo y guardar en un lugar seguro.

#### Restaurar desde un Respaldo

> ⚠️ **Advertencia:** La restauración reemplaza todos los datos actuales. Esta acción no se puede deshacer.

1. Hacer clic en **Restaurar**.
2. Seleccionar el archivo `.json` de respaldo.
3. Ingresar la contraseña de autorización.
4. Confirmar la restauración.

#### Respaldo Automático

Es posible configurar la frecuencia de respaldos automáticos desde el botón **Configurar Auto-Backup**.

---

## 5. Módulo Mesero

El módulo de mesero permite gestionar mesas, tomar pedidos, cobrar cuentas y consultar el historial de ventas personales.

### 5.1 Dashboard del Mesero

Al ingresar se muestra:

- Resumen del día: ventas totales, propinas acumuladas, mesas atendidas.
- Estado en tiempo real de las mesas asignadas.
- Accesos directos a las funciones principales.

---

### 5.2 Mis Mesas

**Ruta:** Menú lateral → **Mis Mesas**

Muestra el estado actual de cada mesa asignada al mesero:

| Estado | Significado |
|--------|------------|
| 🟢 Disponible | Mesa libre, sin cuenta abierta |
| 🔴 Ocupada | Mesa con cuenta activa |
| 🟡 Limpieza | Mesa pendiente de limpieza |

Al hacer clic en una mesa se puede:
- Ver el detalle de la cuenta activa (platillos pedidos, total parcial).
- Acceder a la comanda para agregar más ítems.
- Iniciar el cobro.

---

### 5.3 Comandas Activas

**Ruta:** Menú lateral → **Comandas Activas**

Muestra todas las comandas abiertas del mesero.

#### Abrir una Nueva Cuenta

1. Seleccionar la mesa.
2. Ingresar el número de comensales.
3. Hacer clic en **Abrir Cuenta**.

#### Agregar Ítems a una Comanda

1. Abrir la comanda de la mesa.
2. Navegar por el menú disponible (puede buscar por nombre o categoría).
3. Seleccionar los platillos y la cantidad.
4. Hacer clic en **Enviar a Cocina**.

> Una vez enviados, los ítems aparecen en el panel de cocina en tiempo real.

#### Cerrar una Cuenta

1. Abrir la comanda de la mesa.
2. Hacer clic en **Cerrar Cuenta**.
3. Seleccionar el método de pago:
   - Efectivo
   - Tarjeta
   - Transferencia
   - Mixto
   - Mercado Pago (genera un enlace de pago en línea)
4. Ingresar el monto recibido (si aplica).
5. Registrar propina (opcional).
6. Confirmar el cobro.

La mesa queda disponible automáticamente tras el cierre.

---

### 5.4 Menú

**Ruta:** Menú lateral → **Menú**

Vista de solo lectura del menú actual. Permite consultar platillos disponibles, descripciones y precios. Útil para orientar a los clientes.

---

### 5.5 Propinas del Día

**Ruta:** Menú lateral → **Propinas del Día**

Muestra el acumulado de propinas recibidas en el turno actual, desglosado por cuenta. Incluye gráfica de tendencia por hora.

---

### 5.6 Historial de Cuentas

**Ruta:** Menú lateral → **Historial**

Muestra el historial de cuentas cerradas con filtro por rango de fechas (por defecto, últimos 30 días).

#### Filtrar por Fecha

1. Seleccionar la **Fecha de Inicio** y la **Fecha de Fin** en los campos de filtro.
2. Hacer clic en el ícono de búsqueda (lupa).

#### Gráficas del Historial

- **Ventas por Día:** Total en pesos por cada día del período seleccionado.
- **Propinas por Día:** Propinas recibidas por día.

Hacer clic en **Restablecer** para volver al rango de los últimos 30 días.

---

### 5.7 Segmentación de Mesas (K-Means)

**Ruta:** Menú lateral → **Segmentación**

Esta sección utiliza el algoritmo de **K-Means** para clasificar automáticamente las mesas atendidas en los últimos 90 días en 3 grupos según su comportamiento:

| Cluster | Criterio |
|---------|---------|
| ⭐ Mesas VIP | Alta frecuencia de visitas + ticket promedio alto |
| 🔵 Mesas Regulares | Frecuencia y ticket promedios |
| ⚪ Mesas Ocasionales | Baja frecuencia o ticket bajo |

#### Elementos de la Pantalla

- **Tarjetas Resumen:** Una tarjeta por cluster con el número de mesas, ticket promedio y visitas promedio.
- **Mapa de Clusters:** Gráfica de dispersión donde cada punto es una mesa, coloreado según su cluster.
- **Tabla Detalle:** Lista de todas las mesas con su cluster asignado, visitas, ticket promedio e ingreso total.

> Si se muestran menos de 3 mesas con historial, el sistema indicará que no hay suficientes datos para ejecutar el análisis.

---

## 6. Módulo Cocina

El módulo de cocina está diseñado para recibir y gestionar pedidos en tiempo real sin necesidad de recargar la página.

### 6.1 Dashboard de Cocina

Al ingresar, el panel muestra automáticamente todos los pedidos pendientes ordenados por tiempo de espera. Recibe **alertas sonoras y visuales** cuando llega un nuevo pedido.

#### Alerta de Nuevo Pedido

Cuando el mesero envía una comanda a cocina, aparece automáticamente:
- Una alerta visual (SweetAlert2) con los detalles del pedido.
- Un sonido de notificación.
- El pedido se agrega a la lista de pendientes.

La alerta debe cerrarse manualmente haciendo clic en **Entendido** para confirmar que el personal lo vio.

---

### 6.2 Gestión de Pedidos

**Ruta:** Menú lateral → **Pedidos**

#### Estados de un Pedido

```
Pendiente → En Preparación → Listo → Entregado
```

#### Cambiar el Estado de un Pedido

1. Localizar el pedido en la lista.
2. Hacer clic en el botón correspondiente al siguiente estado:
   - **Iniciar Preparación**: El pedido pasa a "En Preparación".
   - **Marcar como Listo**: El pedido está preparado y listo para llevar.
   - **Marcar como Entregado**: El pedido fue entregado en la mesa.

> Al marcar un pedido como listo, el mesero correspondiente recibe una notificación automática en tiempo real.

---

### 6.3 Vistas de Seguimiento

| Vista | Descripción |
|-------|-------------|
| **Pedidos** | Todos los ítems pendientes de preparación |
| **En Proceso** | Ítems actualmente en preparación |
| **Listos** | Ítems preparados, esperando ser llevados a la mesa |

Cada tarjeta de pedido muestra:
- Número de mesa y nombre del mesero
- Nombre del platillo y cantidad
- **Tiempo de espera** (desde que el ítem fue pedido)
- Indicador visual de urgencia (cambia a rojo cuando lleva mucho tiempo)

---

### 6.4 Gráficas de Inventario (Cocina)

**Ruta:** Menú lateral → **Inventario**

El personal de cocina puede consultar el estado del inventario sin poder modificarlo. Se muestran 4 gráficas:

1. **Estado de Stock:** Insumos en estado normal, bajo y crítico (dona).
2. **Distribución por Categoría:** Cantidad de insumos por categoría (barras).
3. **Historial de Movimientos:** Entradas, salidas, mermas y ajustes por día — últimos 30 días (línea).
4. **Top 5 por Valor:** Los 5 insumos con mayor valor en inventario (barras horizontales).

---

## 7. Módulo Inventario

El módulo de inventario permite llevar el control completo de insumos, registrar movimientos y gestionar proveedores.

### 7.1 Dashboard de Inventario

Muestra un resumen del estado actual del inventario:

- Total de insumos registrados
- Insumos en nivel crítico (stock por debajo del mínimo)
- Valor total del inventario
- Las 4 gráficas de análisis (mismas que ve cocina)
- Alertas activas de stock

---

### 7.2 Gestión de Insumos

**Ruta:** Menú lateral → **Insumos**

#### Registrar un Nuevo Insumo

1. Hacer clic en **Nuevo Insumo**.
2. Completar el formulario:
   - **Nombre** del insumo
   - **Categoría** (carnes, verduras, lácteos, granos, bebidas, condimentos, desechables, limpieza, otros)
   - **Unidad de medida** (kg, gr, lt, ml, pza, caja, paquete)
   - **Stock actual** (cantidad disponible al momento de registrar)
   - **Stock mínimo** (umbral para generar alertas de stock bajo)
   - **Costo unitario**
   - **Proveedor** (opcional)
3. Guardar.

#### Buscar y Filtrar Insumos

Utilizar la barra de búsqueda para localizar insumos por nombre. También es posible filtrar por categoría usando el selector correspondiente.

---

### 7.3 Registro de Movimientos

Cada movimiento queda registrado con fecha, hora, responsable y referencia para trazabilidad completa.

#### Entrada de Inventario

**Ruta:** Menú lateral → **Movimientos → Entrada**

Registra la llegada de insumos (compras a proveedor):

1. Seleccionar el **insumo**.
2. Ingresar la **cantidad** recibida.
3. Ingresar el **costo unitario** (puede diferir del costo base si hay variación de precio).
4. Seleccionar el **proveedor**.
5. Ingresar el número de **referencia/factura** (opcional).
6. Agregar **notas** si es necesario.
7. Registrar.

El stock del insumo se actualiza automáticamente.

#### Salida de Inventario

**Ruta:** Menú lateral → **Movimientos → Salida**

Registra el consumo o uso de insumos:

1. Seleccionar el **insumo**.
2. Ingresar la **cantidad** a descontar.
3. Indicar la **razón** de la salida.
4. Registrar.

#### Merma

**Ruta:** Menú lateral → **Movimientos → Merma**

Registra pérdidas por caducidad, daño o desperdicio:

1. Seleccionar el **insumo**.
2. Ingresar la **cantidad** mermada.
3. Describir la **causa** de la merma.
4. Registrar.

#### Historial de Movimientos

**Ruta:** Menú lateral → **Movimientos → Historial**

Tabla completa de todos los movimientos con:
- Filtro por tipo (entrada, salida, merma, ajuste)
- Filtro por rango de fechas
- Exportable para reportes

---

### 7.4 Alertas de Stock

**Ruta:** Menú lateral → **Alertas**

El sistema genera alertas automáticamente cuando el stock de un insumo cae por debajo del mínimo establecido.

#### Tipos de Alerta

| Tipo | Condición |
|------|-----------|
| **Stock Crítico** | Stock actual ≤ stock mínimo |
| **Stock Bajo** | Stock actual cercano al mínimo |

#### Resolver una Alerta

Una vez que se reabastece el insumo:

1. Localizar la alerta en la lista.
2. Hacer clic en **Resolver**.
3. La alerta queda marcada como resuelta con fecha y hora.

---

### 7.5 Proveedores

**Ruta:** Menú lateral → **Proveedores**

#### Registrar un Proveedor

1. Hacer clic en **Nuevo Proveedor**.
2. Completar: nombre, contacto, teléfono, correo, productos que suministra.
3. Guardar.

Los proveedores registrados quedan disponibles al registrar entradas de inventario.

---

### 7.6 Reportes de Inventario

**Ruta:** Menú lateral → **Reportes**

Muestra las 4 gráficas analíticas del inventario:

| Gráfica | Descripción |
|---------|-------------|
| **Estado de Stock** | Proporción de insumos por estado (normal/bajo/crítico) |
| **Por Categoría** | Distribución de insumos por categoría |
| **Historial de Movimientos** | Línea por tipo (entrada/salida/merma/ajuste) — últimos 30 días |
| **Top 5 por Valor** | Insumos con mayor valor monetario en inventario |

---

## 8. Configuración de Cuenta

Todos los usuarios tienen acceso a la configuración de su propia cuenta.

**Ruta:** Menú lateral → **Configuración** (ícono de engranaje)

### 8.1 Pestaña Perfil

Permite actualizar:
- Nombre y apellidos
- Teléfono de contacto

> El correo electrónico no puede ser modificado por el usuario. Contactar al administrador si es necesario cambiarlo.

### 8.2 Pestaña Seguridad (2FA)

Ver la sección [Autenticación de Dos Factores](#3-autenticación-de-dos-factores-2fa) para el procedimiento completo.

### 8.3 Pestaña Preferencias

Ajustes de visualización y comportamiento de la interfaz según preferencias personales.

---

## 9. Notificaciones

El ícono de campana en la barra superior muestra las notificaciones activas.

### Tipos de Notificaciones

| Tipo | Descripción |
|------|-------------|
| 🟠 Pedido | Nuevo pedido enviado a cocina |
| 🟢 Listo | Pedido listo para llevar a la mesa |
| 🔴 Alerta | Stock crítico de algún insumo |
| ℹ️ Sistema | Inicio/cierre de sesión de personal |

### Gestión de Notificaciones

- **Marcar como leída:** Hacer clic sobre la notificación.
- **Limpiar todo:** Botón "Limpiar todo" en el panel de notificaciones.

El número en rojo sobre la campana indica la cantidad de notificaciones no leídas.

---

## 10. Preguntas Frecuentes

**¿Qué hago si olvidé mi contraseña?**
> Contactar al administrador del sistema para restablecer las credenciales. El sistema no cuenta con recuperación de contraseña por correo en la versión actual.

**¿Por qué no puedo ver ciertas secciones del menú?**
> El acceso a los módulos está determinado por el rol asignado. Si se requiere acceso a una sección adicional, solicitarlo al administrador.

**¿Por qué no llegan las notificaciones de cocina?**
> Verificar que el navegador permita notificaciones del sitio. También asegurarse de que la página esté abierta y la conexión a internet sea estable.

**¿Puedo usar el sistema desde el teléfono?**
> Sí, la interfaz es responsive y funciona en navegadores móviles. Sin embargo, se recomienda usar una pantalla de al menos 10 pulgadas para una experiencia óptima, especialmente en los módulos de cocina y administración.

**¿Qué pasa si se corta el internet durante una comanda?**
> Los datos ya guardados en el servidor no se pierden. Al restablecer la conexión, el sistema retoma el estado actual. Se recomienda no cerrar la pestaña del navegador durante una pérdida de conexión temporal.

**¿Cómo sé si un platillo llegó correctamente a cocina?**
> Una vez enviada la comanda, los ítems aparecen en el panel de cocina en tiempo real. El mesero puede verificar el estado de cada ítem en la vista de la comanda activa.

**¿La aplicación de autenticador es gratuita?**
> Sí. Google Authenticator y Authy son aplicaciones gratuitas disponibles en App Store y Google Play. Solo se requieren una vez para escanear el código QR al activar el 2FA.

**¿Puedo tener más de un dispositivo con el 2FA?**
> Sí, si se usa una aplicación que permita respaldo en la nube como Authy. Con Google Authenticator estándar, solo se puede vincular a un dispositivo por cuenta. En caso de cambio de teléfono, desactivar el 2FA antes del cambio o usar la recuperación de emergencia.

**¿Con qué frecuencia debo hacer respaldos de la base de datos?**
> Se recomienda un respaldo diario, especialmente antes de cierre de turno. El administrador puede configurar respaldos automáticos desde el módulo de Backup.

---

*Manual de Usuario — Restaurante Callejón 9 · Versión 1.0 · Abril 2026*
