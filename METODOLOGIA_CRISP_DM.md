# Metodología CRISP-DM — Restaurante Callejón 9

**Cross-Industry Standard Process for Data Mining** es la metodología estándar de la industria para proyectos de ciencia de datos. Define 6 fases iterativas que guían desde el problema de negocio hasta el modelo en producción. Este sistema las implementa todas sobre las comandas del restaurante.

---

## Mapa de fases

```
[1] Negocio → [2] Datos → [3] Preparación → [4] Modelado → [5] Evaluación → [6] Despliegue
```

---

## Fase 1 — Entendimiento del Negocio

### ¿Qué problema resolvemos?

No todas las mesas son iguales. Algunas generan la mayor parte del ingreso del restaurante; otras rara vez se usan. Sin datos, el mesero trata todas las mesas igual y pierde oportunidades de mejorar el servicio donde más importa.

### Objetivo del sistema

- Clasificar cada mesa en un segmento (VIP, Regular, Ocasional)
- Identificar qué variables definen cada segmento
- Generar recomendaciones accionables por segmento

> **Criterio de éxito:** clusters bien separados (Silhouette Score > 0.4) y reglas interpretables que el mesero pueda entender y aplicar.

---

## Fase 2 — Entendimiento de los Datos

Antes de modelar, exploramos la calidad y distribución de los datos. Los datos provienen de la colección `comandas` en MongoDB — una comanda por cada servicio cerrado.

| Atributo | Valor |
|---|---|
| Fuente | `db.comandas` |
| Ventana temporal | 90 días |
| Unidad de análisis | Por mesa |
| Filtro | `estado: pagada / cerrada` |

### Variables exploradas

| Variable | Campo MongoDB | Cálculo | Uso |
|---|---|---|---|
| Frecuencia | `mesa_numero` | `$sum: 1` por mesa | K-Means + RF |
| Ticket Promedio | `total` | `$avg: "$total"` | K-Means + RF |
| Variabilidad | `total` | `$stdDevPop: "$total"` | Solo RF |
| Propina Promedio | `propina` | `$avg: "$propina"` | Diagnóstico |

---

## Fase 3 — Preparación de los Datos

Los datos crudos no pueden entrar directamente al modelo — las variables tienen escalas muy distintas (frecuencia en decenas, ticket en cientos de pesos). Sin normalización, el K-Means daría más peso a las variables con valores más grandes.

### Pasos del pipeline

1. **Agregación** — Pipeline MongoDB agrupa todas las comandas por `mesa_numero` y calcula el resumen estadístico de cada mesa.
2. **Construcción de features** — Se construye una matriz `X` de forma `n_mesas × 2` para K-Means y `n_mesas × 3` para el Random Forest.
3. **Normalización** — `StandardScaler` transforma cada variable a media=0 y std=1. Así frecuencia y ticket tienen el mismo peso en el clustering.

```python
# Pipeline MongoDB — Fase 3
pipeline = [
    { "$match": { "mesero_id": mesero_oid, "estado": { "$in": ["pagada", "cerrada"] } } },
    { "$group": {
        "_id": "$mesa_numero",
        "num_visitas":     { "$sum": 1 },
        "ticket_promedio": { "$avg": "$total" },
        "ticket_std":      { "$stdDevPop": "$total" }
    } },
]

# Normalización — StandardScaler (sklearn)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_kmeans)  # 2 features
```

---

### Fragmentos de código — dónde ocurre cada paso

#### 1. Limpieza de datos
`services/mesero_kmeans_service.py · línea 46`

Se descartan comandas que no están finalizadas.

```python
# Solo comandas finalizadas en los últimos 90 días
{ "$match": {
    "mesero_id": mesero_oid,
    "estado": { "$in": ["pagada", "cerrada"] },
    "fecha_cierre": { "$gte": hace_n_dias }
} }
```

Elimina comandas con estado `abierta`, `cancelada` o sin `fecha_cierre`. Solo entran al modelo los servicios completamente cerrados dentro de la ventana de 90 días.

---

#### 2. Eliminación de duplicados
`services/mesero_kmeans_service.py · línea 52`

Una fila por mesa, sin importar cuántas comandas tenga.

```python
# $group colapsa N comandas de la misma mesa en 1 sola fila
{ "$group": {
    "_id": "$mesa_numero",   # clave de agrupación
    "num_visitas":      { "$sum": 1 },
    "ticket_promedio":  { "$avg": "$total" },
    "ticket_std":       { "$stdDevPop": "$total" },
    "ingreso_total":    { "$sum": "$total" }
} },
# Mesas con al menos 1 visita (descarta mesas sin historial)
{ "$match": { "num_visitas": { "$gte": 1 } } }
```

El operador `$group` de MongoDB hace la consolidación implícitamente — si Mesa 3 tiene 45 comandas, produce exactamente 1 fila con sus estadísticas agregadas.

---

#### 3. Corrección de errores y valores nulos
`services/mesero_kmeans_service.py · línea 82`

`stdDevPop` devuelve `null` cuando solo hay 1 registro para esa mesa.

```python
# ticket_std es None cuando la mesa solo tiene 1 comanda
X_arbol = np.array([
    [
        float(m["num_visitas"]),
        float(m["ticket_promedio"]),
        float(m.get("ticket_std") or 0),  # None → 0
    ]
    for m in mesas_raw
])

# Guardia: K-Means necesita al menos 3 mesas distintas
if len(mesas_raw) < 3:
    return { "puntos": [], "aviso": "Se necesitan al menos 3 mesas..." }
```

`m.get("ticket_std") or 0`: si `$stdDevPop` devuelve `None` o `0.0`, el resultado es `0` — variabilidad nula, comanda única.

---

#### 4. Transformación de formatos
`services/mesero_kmeans_service.py · línea 74`

De documentos MongoDB a matrices NumPy.

```python
# Formato entrada: lista de dicts MongoDB
# mesas_raw = [{"_id": 3, "num_visitas": 45, "ticket_promedio": 162.5, ...}, ...]

# Formato K-Means: matriz 2D  →  shape (n_mesas, 2)
X_kmeans = np.array([
    [float(m["num_visitas"]), float(m["ticket_promedio"])]
    for m in mesas_raw
])

# Formato Random Forest: matriz 3D  →  shape (n_mesas, 3)
X_arbol = np.array([
    [float(m["num_visitas"]), float(m["ticket_promedio"]), float(m.get("ticket_std") or 0)]
    for m in mesas_raw
])
```

Los documentos BSON de MongoDB se convierten a `float` explícitamente para evitar errores de tipo con `Decimal128` o campos `int` de MongoDB que NumPy no acepta directamente.

---

#### 5. Transformación de los datos
`services/mesero_kmeans_service.py · línea 88`

Normalización y reordenamiento de etiquetas.

```python
# Paso A — Z-score: media=0, desviación=1 por columna
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X_kmeans)
# Antes: Frecuencia=[2..80], Ticket=[120..480]
# Después: ambas variables en escala [-2, +2] aprox.

# Paso B — Reordenar clusters para que 0=VIP, 1=Regular, 2=Ocasional
# (K-Means asigna números de cluster aleatoriamente en cada ejecución)
centroids_orig = scaler.inverse_transform(km.cluster_centers_)
orden          = np.argsort(centroids_orig[:, 0] + centroids_orig[:, 1])[::-1]
remap          = { old: new for new, old in enumerate(orden) }
labels_remap   = np.array([remap[l] for l in km.labels_])
```

**Paso A:** sin normalización, Ticket (ej. 350 MXN) dominaría sobre Frecuencia (ej. 8 visitas) solo por ser un número más grande.  
**Paso B:** K-Means no garantiza que el cluster 0 siempre sea VIP — se reordenan los labels por `visitas + ticket` descendente para mantener la nomenclatura consistente entre ejecuciones.

---

## Fase 4 — Modelado: K-Means + Random Forest

### Paso 1 — K-Means (no supervisado)

K-Means agrupa los datos en **k=3 clusters** minimizando la distancia de cada punto a su centroide (punto central del grupo).

El algoritmo repite dos pasos hasta converger:
1. **Asignación:** cada mesa se asigna al centroide más cercano
2. **Actualización:** el centroide se mueve al promedio de su grupo

Parámetros: `n_clusters=3, n_init=10, random_state=42`

**¿Por qué k=3?**  
El **método del codo** grafica la inercia (suma de distancias al centroide) para k=1,2,3,4,5. En k=3 la curva forma un "codo" — agregar más clusters reduce poco la inercia pero aumenta la complejidad.

**Orden de clusters**  
Después del clustering, los clusters se reordenan por `visitas + ticket` descendente, así el cluster 0 siempre es VIP y el 2 siempre Ocasional.

---

### Paso 2 — Random Forest (supervisado)

Los labels generados por K-Means se usan como variable objetivo para entrenar un **Random Forest de 200 árboles**.

Cada árbol se entrena sobre un subconjunto aleatorio de los datos (*bootstrap sampling*) con 3 features. Al promediar 200 árboles:
- Se reduce la varianza (menos sensible a datos atípicos)
- La importancia de features se distribuye entre todas las variables
- Se evita el sobreajuste típico de un árbol único

Parámetros: `n_estimators=200, max_depth=3, oob_score=True`

**¿Por qué 3 features en el RF y 2 en K-Means?**  
K-Means usa **Frecuencia + Ticket** (2D) para crear clusters interpretables en el scatter plot. El RF usa además **Variabilidad** (`stdDevPop` del ticket) para intentar distinguir VIP (gasto irregular alto) de Regular (gasto estable medio) dentro del grupo de alta frecuencia.

**Árbol representativo**  
Para visualizar las reglas, se muestra el árbol individual del bosque cuyas importancias de features más se acercan al promedio de los 200.

---

## Fase 5 — Evaluación

### Silhouette Score

Mide qué tan bien separados están los clusters. Para cada punto calcula la distancia promedio a su propio cluster (*a*) y al cluster más cercano (*b*).

```
score = (b − a) / max(a, b)
```

| Valor | Interpretación |
|---|---|
| Cercano a 1 | Clusters muy separados |
| Cercano a 0 | Clusters solapados |
| Negativo | Asignación incorrecta |

### Inercia (Método del Codo)

Suma de las distancias al cuadrado de cada punto a su centroide. A más clusters, menor inercia — pero el objetivo es encontrar el punto donde reducir más clusters ya no vale la pena.

El "codo" en la gráfica marca ese punto óptimo. Para este restaurante el codo aparece en **k=3**.

### OOB Score (Random Forest)

*Out-of-Bag Score* — cada árbol se entrena dejando fuera ~37% de los datos (los que no entraron en su bootstrap). Esos datos se usan para validar el árbol sin necesitar un conjunto de prueba separado.

Un OOB Score de **0.75** significa que el bosque clasifica correctamente el 75% de las mesas que no vio durante su entrenamiento.

---

## Fase 6 — Despliegue

El modelo corre en producción dentro del servidor Flask. No requiere reentrenamiento manual — cada vez que el mesero abre la página de Segmentación, el sistema recalcula los clusters con las últimas comandas de los 90 días anteriores.

### Flujo de una petición

1. **Mesero abre `/mesero/kmeans`** — El navegador carga la página HTML
2. **JavaScript hace `GET /api/mesero/kmeans`** — Petición autenticada con sesión Flask
3. **`MeseroKMeansService.segmentar_mesas()`** — Ejecuta pipeline MongoDB → K-Means → RF
4. **JSON de respuesta** — puntos, resumen, evaluación, árbol representativo
5. **Chart.js renderiza el scatter** — El mesero ve su mapa de clusters actualizado

### Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/mesero/kmeans` | Ejecuta K-Means + RF, devuelve JSON |
| GET | `/api/mesero/kmeans/diagnostico` | Estadísticas Fase 2 |
| GET | `/mesero/kmeans` | Vista de segmentación |
| GET | `/mesero/arbol` | Vista Random Forest |
| GET | `/mesero/diagnostico` | Vista de diagnóstico |
| GET | `/mesero/metodologia` | Esta documentación |

---

## Arquitectura del Pipeline

```
MongoDB        →   Agregación       →   K-Means    →   Random Forest    →   Dashboard
(db.comandas)      + StandardScaler     k=3 (2D)       200 árboles (3D)     JSON + Chart.js
```

### Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `services/mesero_kmeans_service.py` | Toda la lógica de datos y modelos |
| `controllers/mesero/kmeans_controller.py` | Rutas → servicio → respuesta |
| `routes/mesero_routes.py` | Registro de URLs y middlewares |
| `resources/views/mesero/mesero_kmeans.html` | Vista Segmentación (K-Means) |
| `resources/views/mesero/mesero_arbol.html` | Vista Random Forest |
| `resources/views/mesero/mesero_diagnostico.html` | Vista Diagnóstico (Fase 2) |
| `scripts/seed_data.py` | Generación de datos de prueba con 3 clusters reales |
