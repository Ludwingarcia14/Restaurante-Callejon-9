# 🚀 Pyme – Plataforma de Gestión Financiera Inteligente

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-Framework-black)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![CQRS](https://img.shields.io/badge/Architecture-CQRS-success)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Descripción General

**Pyme** es una plataforma financiera de nivel **enterprise** diseñada para la gestión inteligente de créditos y préstamos dirigidos a **Pymes y clientes particulares**.

Integra:
- Arquitectura **CQRS**
- Procesamiento documental automatizado
- **Motor de Inteligencia Artificial**
- Análisis de riesgo financiero previo a validación humana

El sistema está pensado para **escalar**, **auditar** y **automatizar** procesos críticos del sector financiero.

---

## 🧱 Arquitectura General (Enterprise)

```text
┌──────────────┐
│   Frontend   │  (Bulma + JS)
└──────┬───────┘
       │ HTTP / Auth
┌──────▼────────┐
│    Flask API  │
│ (Controllers) │
└──────┬────────┘
       │
┌──────▼───────────────┐
│        CQRS          │
│  Commands / Queries  │
└──────┬───────────────┘
       │
┌──────▼──────────┐
│  Services Layer │
│ Business Logic  │
└──────┬──────────┘
       │
┌──────▼────────────┐
│   AI Engine       │
│ OCR + Analysis    │
└──────┬────────────┘
       │
┌──────▼────────┐
│   MySQL DB     │
│ SQLAlchemy    │
└───────────────┘
```

---

## 📋 Características Clave

### 🔐 Seguridad y Control
- Autenticación por sesión
- Roles y permisos
- Aislamiento de responsabilidades

### 💳 Gestión de Créditos
- Solicitudes
- Estados
- Evaluación automatizada
- Validación humana final

### 🧠 AI Engine
- OCR automático con **Poppler + Tesseract**
- Fallback PyMuPDF
- Clasificación documental
- Extracción estructurada
- Normalización de texto
- Validaciones cruzadas

---

## 🧠 Documentación Interna – AI Engine

📂 `services/ai_engine/`

### 🔄 Flujo de Procesamiento

```text
Documento PDF
     │
     ▼
¿PDF tiene texto?
     │
 ┌───┴────┐
 │        │
NO       SI
 │        │
 ▼        ▼
OCR     PyMuPDF
 │        │
 └───┬────┘
     ▼
Normalización
     ▼
Clasificación
     ▼
Extracción
     ▼
Validaciones
     ▼
Resultado JSON
```

### 📑 Tipos de Documentos Soportados
- INE / Identificaciones
- Estados de Cuenta Bancarios
- Buró de Crédito
- Comprobantes:
  - CFE
  - Telmex
  - Agua
  - Predial

### 🧪 Estrategias Técnicas
- Limpieza Unicode
- Regex financieros
- Fechas dinámicas
- Detección de proveedor
- Manejo de PDFs escaneados

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|-----|------------|
| Backend | Python 3.11 |
| Framework | Flask |
| DB | MySQL |
| ORM | SQLAlchemy |
| IA | Tesseract, OpenCV |
| OCR | Poppler |
| Infra | Docker |

---

## 📂 Estructura del Proyecto

```text
├── config/
├── controllers/
├── cqrs/
│   ├── commands/
│   └── queryes/
├── services/
│   └── ai_engine/
├── models/
├── utils/
├── static/
├── resources/views/
├── app.py
└── routes.py
```

---

## 🚀 Instalación

```bash
git clone <repo>
cd pyme
conda create -n miniconda311 python=3.11 -y
conda activate miniconda311
pip install -r requirements.txt
cp .env.example .env
python app.py
```

---

## 🐳 Docker

```bash
docker build -t pyme-app .
docker run -d -p 5000:5000 --env-file .env pyme-app
```

---

## 📜 Licencia

MIT License

---
---

## 👨‍💻 Equipo de Desarrollo

### 🔐 Core Team

**Flores Vargas Edwin**  
- Rol: **Lead / Maintainer**
- Cargo: Project Manager  
- Responsabilidades: Dirección del proyecto, planificación, coordinación general  

**Mora Ortega Jennyfer**  
- Rol: **Lead / Maintainer**
- Cargo: Líder de Proyecto & Project Manager  
- Responsabilidades: Gestión del proyecto, toma de decisiones técnicas y estratégicas  

---

### 🤝 Equipo de Desarrollo (Contributors)

**Carlos Hernandez Josselin**  
- Rol: Contributor  
- Cargo: Developer  

**Garcia Gaytan Ludwin**  
- Rol: Contributor  
- Cargo: Developer  

**Jimenez Olvera Alberto**  
- Rol: Contributor  
- Cargo: Developer  

---

## 👨‍💻 Autor

**POTENCIAL PYME**  
Arquitectura, Backend, AI Engine

---

> Plataforma diseñada para entornos financieros reales, escalables y auditables.
