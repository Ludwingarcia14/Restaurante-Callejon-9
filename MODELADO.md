# Modelado — K-Means + Random Forest

Documentación técnica del módulo de machine learning del Restaurante Callejón 9.  
Archivos principales: `services/mesero_kmeans_service.py` · `services/mesero_randomforest_service.py`

---

## Enfoque híbrido

El sistema usa dos modelos en secuencia:

```
Comandas MongoDB
      │
      ▼
  K-Means (no supervisado)
  Agrupa mesas por similitud → genera etiquetas (0, 1, 2)
      │
      ▼
  Random Forest (supervisado)
  Aprende esas etiquetas → distribuye importancia entre features
      │
      ▼
  Dashboard: segmentos, reglas, métricas
```

**¿Por qué dos modelos?**  
K-Means crea los grupos automáticamente sin necesitar etiquetas previas. El problema es que un solo árbol de decisión entrenado sobre datos bien separados ignoraría algunas variables. El Random Forest (200 árboles con muestras aleatorias) distribuye la importancia entre todos los features y da una estimación de confianza (OOB Score) sin necesitar un conjunto de prueba separado.

---

## Features (variables de entrada)

Los datos vienen de la colección `comandas` en MongoDB, agrupados por mesa en los últimos 90 días.

| Feature | Cálculo MongoDB | Usado en |
|---|---|---|
| `Frecuencia` | `$sum: 1` — número de comandas cerradas | K-Means + RF |
| `Ticket Promedio` | `$avg: "$total"` — promedio del total facturado | K-Means + RF |
| `Variabilidad` | `$stdDevPop: "$total"` — desviación estándar del ticket | Solo RF |

**K-Means usa 2 features** (espacio 2D, visualizable en scatter plot).  
**Random Forest usa 3 features** (agrega Variabilidad para distinguir mesas con gasto irregular).

---

## Paso 1 — Extracción de datos

```python
# services/mesero_kmeans_service.py

pipeline = [
    {"$match": {
        "mesero_id": mesero_oid,
        "estado": {"$in": ["pagada", "cerrada"]},   # solo comandas finalizadas
        "fecha_cierre": {"$gte": hace_n_dias}        # ventana de 90 días
    }},
    {"$group": {
        "_id": "$mesa_numero",
        "num_visitas":      {"$sum": 1},
        "ticket_promedio":  {"$avg": "$total"},
        "ticket_std":       {"$stdDevPop": "$total"},
        "propina_promedio": {"$avg": "$propina"},
        "ingreso_total":    {"$sum": "$total"}
    }},
    {"$match": {"num_visitas": {"$gte": 1}}},
    {"$sort": {"ingreso_total": -1}}
]
mesas_raw = list(db.comandas.aggregate(pipeline))
```

El resultado es una lista de diccionarios, uno por mesa. Antes de entrar al modelo se valida el mínimo requerido:

```python
if len(mesas_raw) < 3:
    return {
        "puntos": [], "resumen": [],
        "aviso": "Se necesitan al menos 3 mesas con historial para ejecutar K-Means."
    }
```

---

## Paso 2 — Construcción de matrices

Se convierten los documentos MongoDB a matrices NumPy. Los valores se castean a `float` explícitamente para evitar errores con tipos BSON (`Decimal128`, `int64`).

```python
# Matriz para K-Means: shape (n_mesas, 2)
X_kmeans = np.array([
    [float(m["num_visitas"]), float(m["ticket_promedio"])]
    for m in mesas_raw
])

# Matriz para Random Forest: shape (n_mesas, 3)
# ticket_std puede ser None si la mesa tiene solo 1 comanda → se reemplaza por 0
X_arbol = np.array([
    [
        float(m["num_visitas"]),
        float(m["ticket_promedio"]),
        float(m.get("ticket_std") or 0),
    ]
    for m in mesas_raw
])
```

---

## Paso 3 — Normalización (StandardScaler)

K-Means mide distancias euclidianas. Sin normalizar, una variable con valores grandes (ticket: 350 MXN) dominaría sobre una con valores pequeños (frecuencia: 8 visitas) aunque ambas sean igualmente importantes.

`StandardScaler` transforma cada columna a **media = 0, desviación estándar = 1**:

```python
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_kmeans)

# Antes:  Frecuencia=[2..80],  Ticket=[120..480]
# Después: ambas columnas en escala [-2, +2] aprox.
```

> El scaler se aplica **solo a K-Means**. El Random Forest recibe `X_arbol` sin escalar porque los árboles de decisión son invariantes a la escala.

---

## Paso 4 — K-Means

```python
k = min(3, len(mesas_raw))  # k=3, o menos si hay pocas mesas

km = KMeans(
    n_clusters=k,
    random_state=42,   # reproducibilidad
    n_init=10          # reintentos con distintos centroides iniciales
)
km.fit(X_scaled)
```

**Parámetros clave**

| Parámetro | Valor | Motivo |
|---|---|---|
| `n_clusters` | 3 | VIP, Regular, Ocasional — validado con método del codo |
| `n_init` | 10 | Reduce la probabilidad de converger en un mínimo local |
| `random_state` | 42 | Resultados reproducibles entre ejecuciones |

### Método del codo (elbow)

Se calcula la inercia para k=1 hasta k=5 para confirmar que k=3 es el punto óptimo:

```python
elbow = []
for ki in range(1, min(6, len(mesas_raw))):
    ki_km = KMeans(n_clusters=ki, random_state=42, n_init=10)
    ki_km.fit(X_scaled)
    elbow.append({"k": ki, "inertia": round(float(ki_km.inertia_), 4)})
```

La inercia es la suma de distancias al cuadrado de cada punto a su centroide. El "codo" aparece donde agregar más clusters deja de reducir significativamente la inercia.

### Reordenamiento de clusters

K-Means asigna números de cluster aleatoriamente en cada ejecución. Se reordenan para que el cluster 0 sea siempre VIP y el 2 siempre Ocasional:

```python
# Desescalar los centroides para compararlos en unidades originales
centroids_orig = scaler.inverse_transform(km.cluster_centers_)

# Ordenar por (frecuencia + ticket) descendente → el más alto es VIP
orden = np.argsort(centroids_orig[:, 0] + centroids_orig[:, 1])[::-1]

# Crear mapa de reasignación: {cluster_original: cluster_nuevo}
remap = {old: new for new, old in enumerate(orden)}

# Aplicar el remap a todos los labels
labels_remap = np.array([remap[l] for l in km.labels_])
```

### Evaluación — Silhouette Score

```python
if k >= 2 and len(mesas_raw) > k:
    sil_score = round(float(silhouette_score(X_scaled, km.labels_)), 4)
```

El Silhouette Score mide qué tan bien separados están los clusters:

```
score = (b − a) / max(a, b)
```

- `a` = distancia promedio al propio cluster
- `b` = distancia promedio al cluster más cercano
- Rango: [-1, 1] — valores > 0.4 indican clusters bien separados

---

## Paso 5 — Random Forest

El Random Forest recibe las etiquetas generadas por K-Means como variable objetivo (`y = labels_remap`) y aprende a predecirlas usando las 3 features.

```python
# services/mesero_randomforest_service.py

rf = RandomForestClassifier(
    n_estimators=200,   # 200 árboles en el bosque
    max_depth=3,        # profundidad máxima por árbol
    random_state=42,
    oob_score=True,     # activa validación out-of-bag
)
rf.fit(X_raw, labels)
```

**Parámetros clave**

| Parámetro | Valor | Motivo |
|---|---|---|
| `n_estimators` | 200 | Suficientes árboles para estabilizar las importancias |
| `max_depth` | 3 | Árboles simples e interpretables, evita sobreajuste |
| `oob_score` | True | Validación gratuita sin conjunto de prueba separado |

### Bootstrap sampling

Cada uno de los 200 árboles se entrena sobre una muestra aleatoria con reemplazo (~63% de los datos). El ~37% restante (out-of-bag) se usa para estimar el error sin necesitar un conjunto de validación externo.

### Importancia de features

```python
imp_mean = rf.feature_importances_   # promedio de los 200 árboles

# Desviación estándar entre árboles: mide la estabilidad de cada feature
imp_std = np.std([t.feature_importances_ for t in rf.estimators_], axis=0)

importancias = sorted(
    [
        {
            "feature":     _FEATURE_LABELS[i],    # "Frecuencia", "Ticket Promedio", "Variabilidad"
            "importancia": round(float(imp_mean[i]), 4),
            "std":         round(float(imp_std[i]), 4),
        }
        for i in range(len(_FEATURE_LABELS))
    ],
    key=lambda x: x["importancia"],
    reverse=True,
)
```

El resultado típico con los datos del restaurante:

```
Frecuencia      ~39%  ± std
Ticket Promedio ~33%  ± std
Variabilidad    ~28%  ± std
```

La variabilidad en el ticket es un indicador de mesas VIP (gasto irregular alto) que un árbol único ignoraría.

### Árbol representativo

En lugar de mostrar un árbol aleatorio del bosque, se selecciona el que más se acerca al promedio del ensemble:

```python
diffs = [
    float(np.sum((t.feature_importances_ - imp_mean) ** 2))
    for t in rf.estimators_
]
arbol_rep = rf.estimators_[int(np.argmin(diffs))]
reglas = export_text(arbol_rep, feature_names=_FEATURE_LABELS)
```

`export_text` genera una representación legible de las reglas del árbol:

```
|--- Frecuencia <= 12.50
|   |--- Ticket Promedio <= 180.00
|   |   |--- class: Mesas Ocasionales
|   |--- Ticket Promedio > 180.00
|   |   |--- class: Mesas Regulares
|--- Frecuencia > 12.50
|   |--- class: Mesas VIP
```

### OOB Score

```python
oob_score = round(float(rf.oob_score_), 4)
```

Precisión estimada del bosque sobre los datos que cada árbol no vio durante su entrenamiento. Un OOB Score de 0.80 significa que el modelo clasifica correctamente el 80% de los casos fuera de muestra.

---

## Paso 6 — Construcción de la respuesta

```python
return {
    "puntos": puntos,        # lista de mesas con cluster, coordenadas y metadata
    "resumen": resumen,      # estadísticas agregadas por cluster
    "periodo_dias": dias,    # 90
    "evaluacion": {
        "silhouette_score": sil_score,
        "inertia":          round(float(km.inertia_), 4),
        "n_mesas":          len(mesas_raw),
        "n_clusters":       k,
        "elbow":            elbow,   # lista [{k, inertia}, ...]
    },
    "arbol": {
        "reglas":              reglas,         # texto del árbol representativo
        "feature_importances": importancias,   # [{feature, importancia, std}, ...]
        "clases":              nombres_clase,  # ["Mesas VIP", "Mesas Regulares", "Mesas Ocasionales"]
        "n_estimators":        200,
        "oob_score":           oob_score,
    }
}
```

---

## Flujo completo resumido

```
db.comandas.aggregate(pipeline)
        │
        ▼
mesas_raw  →  X_kmeans (n×2)  →  StandardScaler  →  KMeans(k=3)
                                                          │
                                                    labels_remap
                                                          │
mesas_raw  →  X_arbol  (n×3)  ──────────────────►  RandomForest(200)
                                                          │
                                             importancias + reglas + oob_score
```

---

## Archivos involucrados

| Archivo | Responsabilidad |
|---|---|
| `services/mesero_kmeans_service.py` | Pipeline MongoDB, normalización, K-Means, Silhouette, Elbow |
| `services/mesero_randomforest_service.py` | Entrenamiento RF, importancias, árbol representativo |
| `controllers/mesero/kmeans_controller.py` | Expone `api_kmeans()` → llama al servicio K-Means |
| `routes/mesero_routes.py` | Registra `GET /api/mesero/kmeans` |
| `resources/views/mesero/mesero_kmeans.html` | Scatter plot, resumen de clusters, elbow chart |
| `resources/views/mesero/mesero_arbol.html` | Importancias, OOB Score, reglas del árbol |
