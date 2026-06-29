"""
Seed del menú — Restaurante Callejón 9
Inserta 52 platillos en db.platillos con el esquema completo del modelo.

Uso:
    python seed_productos.py          # inserta/actualiza platillos
    python seed_productos.py --reset  # borra todo y re-inserta
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from config.db import db

AHORA = datetime.utcnow()

# ---------------------------------------------------------------------------
# Catálogo — 52 platillos distribuidos en 5 categorías
# categoria slug: entrada | plato_fuerte | bebida | postre | especial
# ---------------------------------------------------------------------------

BASE_IMG = "/static/images/menu/"

# Imágenes específicas por platillo
_IMG = {
    "Guacamole con Tostadas":      "guacamole.jpg",
    "Sopecitos de Tinga (3)":      "sopes_pollo.jpg",
    "Tacos al Pastor (5)":         "tacos_al_pastor.jpg",
    "Enchiladas Suizas":           "enchiladas.jpg",
    "Chilaquiles Rojos":           "chilaquiles.jpg",
    "Quesadillas de Tinga (2)":    "quesadilla_champis.jpeg",
    "Agua del Día":                "agua_horchata.jpg",
    "Agua de Jamaica":             "agua_horchata.jpg",
    "Café de Olla":                "capuccino.jpg",
    "Flan Napolitano":             "flan.jpg",
}

# Imagen de categoría como fallback (para platillos sin imagen propia)
_CAT_IMG = {
    "entrada":      "guacamole.jpg",
    "plato_fuerte": "tacos_al_pastor.jpg",
    "bebida":       "agua_horchata.jpg",
    "postre":       "flan.jpg",
    "especial":     "enchiladas.jpg",
}

PLATILLOS = [
    # ── ENTRADAS (10) ───────────────────────────────────────────────────────
    {
        "nombre": "Guacamole con Tostadas",
        "descripcion": "Aguacate Hass, jitomate, cebolla, cilantro y limón. Sirve con tostadas artesanales.",
        "categoria": "entrada", "precio": 85.0,
        "tiempo_preparacion": 8, "nivel_picante": 1,
    },
    {
        "nombre": "Queso Fundido con Chorizo",
        "descripcion": "Queso Oaxaca derretido con chorizo de hoja al comal. Sirve con tortillas.",
        "categoria": "entrada", "precio": 115.0,
        "tiempo_preparacion": 10, "nivel_picante": 1,
    },
    {
        "nombre": "Elotes Callejeros",
        "descripcion": "Elote en vaso con mayonesa, queso cotija, chile y limón.",
        "categoria": "entrada", "precio": 55.0,
        "tiempo_preparacion": 5, "nivel_picante": 1,
    },
    {
        "nombre": "Totopos con Salsa y Frijoles",
        "descripcion": "Totopos de maíz azul con salsa verde tatemada y frijoles negros.",
        "categoria": "entrada", "precio": 50.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
    },
    {
        "nombre": "Ceviche de Camarón",
        "descripcion": "Camarón fresco marinado en limón, jitomate, pepino y habanero.",
        "categoria": "entrada", "precio": 155.0,
        "tiempo_preparacion": 15, "nivel_picante": 2,
        "alergenos": ["mariscos"],
    },
    {
        "nombre": "Flautas de Papa (3)",
        "descripcion": "Flautas de maíz rellenas de papa con crema y salsa verde.",
        "categoria": "entrada", "precio": 75.0,
        "tiempo_preparacion": 12, "nivel_picante": 0,
    },
    {
        "nombre": "Sopa de Lima",
        "descripcion": "Caldo de pollo con lima, tortilla frita, aguacate y chile serrano.",
        "categoria": "entrada", "precio": 85.0,
        "tiempo_preparacion": 10, "nivel_picante": 1,
    },
    {
        "nombre": "Esquites Especiales",
        "descripcion": "Maíz cacahuazintle, epazote, crema, queso cotija y chile de árbol.",
        "categoria": "entrada", "precio": 65.0,
        "tiempo_preparacion": 8, "nivel_picante": 2,
    },
    {
        "nombre": "Alitas BBQ (6)",
        "descripcion": "Alitas de pollo horneadas con salsa BBQ de la casa.",
        "categoria": "entrada", "precio": 125.0,
        "tiempo_preparacion": 20, "nivel_picante": 1,
    },
    {
        "nombre": "Sopecitos de Tinga (3)",
        "descripcion": "Sopes de masa azul con tinga de pollo, lechuga, crema y queso.",
        "categoria": "entrada", "precio": 95.0,
        "tiempo_preparacion": 12, "nivel_picante": 1,
    },

    # ── PLATOS FUERTES (17) ─────────────────────────────────────────────────
    {
        "nombre": "Tacos al Pastor (5)",
        "descripcion": "Cerdo marinado en achiote y chile guajillo, piña, cebolla y cilantro.",
        "categoria": "plato_fuerte", "precio": 95.0,
        "tiempo_preparacion": 10, "nivel_picante": 1,
    },
    {
        "nombre": "Enchiladas Suizas",
        "descripcion": "Tortillas bañadas en salsa verde con pollo, crema y queso gratinado.",
        "categoria": "plato_fuerte", "precio": 130.0,
        "tiempo_preparacion": 15, "nivel_picante": 1,
    },
    {
        "nombre": "Hamburguesa BBQ",
        "descripcion": "Carne angus 200g, tocino, queso cheddar, cebolla caramelizada y papas.",
        "categoria": "plato_fuerte", "precio": 145.0,
        "tiempo_preparacion": 18, "nivel_picante": 0,
    },
    {
        "nombre": "Pollo a la Parrilla",
        "descripcion": "Pechuga marinada en cítricos con arroz rojo, frijoles y ensalada.",
        "categoria": "plato_fuerte", "precio": 165.0,
        "tiempo_preparacion": 20, "nivel_picante": 0,
    },
    {
        "nombre": "Costillas BBQ",
        "descripcion": "Costillas de cerdo ahumadas 6 horas con salsa BBQ, coleslaw y papas.",
        "categoria": "plato_fuerte", "precio": 225.0,
        "tiempo_preparacion": 25, "nivel_picante": 0,
    },
    {
        "nombre": "Chilaquiles Rojos",
        "descripcion": "Totopos en salsa roja, pollo deshebrado, crema, queso y cebolla morada.",
        "categoria": "plato_fuerte", "precio": 100.0,
        "tiempo_preparacion": 12, "nivel_picante": 2,
    },
    {
        "nombre": "Pozole Rojo",
        "descripcion": "Caldo de maíz cacahuazintle con cerdo, orégano y guarniciones.",
        "categoria": "plato_fuerte", "precio": 125.0,
        "tiempo_preparacion": 10, "nivel_picante": 1,
    },
    {
        "nombre": "Burritos de Res",
        "descripcion": "Tortilla de harina XXL con arrachera, frijoles, queso, pico de gallo y crema.",
        "categoria": "plato_fuerte", "precio": 135.0,
        "tiempo_preparacion": 15, "nivel_picante": 1,
    },
    {
        "nombre": "Quesadillas de Tinga (2)",
        "descripcion": "Quesadillas de maíz con tinga de pollo, queso Oaxaca y rajas.",
        "categoria": "plato_fuerte", "precio": 115.0,
        "tiempo_preparacion": 12, "nivel_picante": 1,
    },
    {
        "nombre": "Tlayuda Oaxaqueña",
        "descripcion": "Tortilla grande crujiente con frijoles, tasajo, quesillo y chapulines.",
        "categoria": "plato_fuerte", "precio": 160.0,
        "tiempo_preparacion": 18, "nivel_picante": 0,
    },
    {
        "nombre": "Arrachera a la Parrilla",
        "descripcion": "300g de arrachera marinada con nopales, cebollitas, guacamole y tortillas.",
        "categoria": "plato_fuerte", "precio": 255.0,
        "tiempo_preparacion": 22, "nivel_picante": 0,
    },
    {
        "nombre": "Milanesa de Res",
        "descripcion": "Milanesa empanizada de res con papas fritas, ensalada y salsa de la casa.",
        "categoria": "plato_fuerte", "precio": 175.0,
        "tiempo_preparacion": 20, "nivel_picante": 0,
    },
    {
        "nombre": "Pescado a la Veracruzana",
        "descripcion": "Filete al horno en salsa con jitomate, aceitunas, alcaparras y chiles.",
        "categoria": "plato_fuerte", "precio": 185.0,
        "tiempo_preparacion": 22, "nivel_picante": 1,
        "alergenos": ["pescado"],
    },
    {
        "nombre": "Camarones al Ajillo",
        "descripcion": "Camarones jumbo salteados en mantequilla, ajo, limón y chile de árbol.",
        "categoria": "plato_fuerte", "precio": 200.0,
        "tiempo_preparacion": 15, "nivel_picante": 2,
        "alergenos": ["mariscos"],
    },
    {
        "nombre": "Torta Ahogada",
        "descripcion": "Birote con carnitas bañado en salsa de jitomate y chile de árbol.",
        "categoria": "plato_fuerte", "precio": 120.0,
        "tiempo_preparacion": 10, "nivel_picante": 3,
    },
    {
        "nombre": "Tacos de Canasta (5)",
        "descripcion": "Papa, frijol y chicharrón prensado en tortilla blanda.",
        "categoria": "plato_fuerte", "precio": 75.0,
        "tiempo_preparacion": 8, "nivel_picante": 0,
    },
    {
        "nombre": "Enfrijoladas de Pollo",
        "descripcion": "Tortillas en salsa de frijol negro con pollo, queso fresco y crema.",
        "categoria": "plato_fuerte", "precio": 115.0,
        "tiempo_preparacion": 14, "nivel_picante": 0,
    },

    # ── BEBIDAS (12) ────────────────────────────────────────────────────────
    {
        "nombre": "Cerveza Corona",
        "descripcion": "Cerveza rubia 355ml.",
        "categoria": "bebida", "precio": 45.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
        "alergenos": ["gluten"],
    },
    {
        "nombre": "Cerveza Modelo Negra",
        "descripcion": "Cerveza oscura 355ml.",
        "categoria": "bebida", "precio": 50.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
        "alergenos": ["gluten"],
    },
    {
        "nombre": "Refresco de Vidrio",
        "descripcion": "Coca-Cola, Sprite o Sangría en botella de vidrio 355ml.",
        "categoria": "bebida", "precio": 35.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
    },
    {
        "nombre": "Agua del Día",
        "descripcion": "Agua fresca de temporada: jamaica, horchata, tamarindo o guayaba.",
        "categoria": "bebida", "precio": 35.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
    },
    {
        "nombre": "Michelada Clásica",
        "descripcion": "Cerveza con limón, salsa inglesa, clamato y chamoy. Vaso escaramujo.",
        "categoria": "bebida", "precio": 80.0,
        "tiempo_preparacion": 3, "nivel_picante": 1,
        "alergenos": ["gluten"],
    },
    {
        "nombre": "Margarita Clásica",
        "descripcion": "Tequila blanco, triple seco, jugo de limón y sal en vaso escaramujo.",
        "categoria": "bebida", "precio": 100.0,
        "tiempo_preparacion": 3, "nivel_picante": 0,
    },
    {
        "nombre": "Limonada con Chía",
        "descripcion": "Limonada natural con semillas de chía y hierbabuena.",
        "categoria": "bebida", "precio": 50.0,
        "tiempo_preparacion": 2, "nivel_picante": 0,
    },
    {
        "nombre": "Agua de Jamaica",
        "descripcion": "Jamaica concentrada con poca azúcar y naranja.",
        "categoria": "bebida", "precio": 35.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
    },
    {
        "nombre": "Café de Olla",
        "descripcion": "Café con canela, piloncillo y clavo de olor. Jarra de barro.",
        "categoria": "bebida", "precio": 45.0,
        "tiempo_preparacion": 3, "nivel_picante": 0,
    },
    {
        "nombre": "Mezcal Artesanal (shot)",
        "descripcion": "Mezcal joven de Oaxaca con naranja y sal de gusano.",
        "categoria": "bebida", "precio": 90.0,
        "tiempo_preparacion": 1, "nivel_picante": 0,
    },
    {
        "nombre": "Sangría de la Casa",
        "descripcion": "Vino tinto, jugo de naranja, frutas de temporada y canela. Jarra 1L.",
        "categoria": "bebida", "precio": 175.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
        "alergenos": ["sulfitos"],
    },
    {
        "nombre": "Jugo Verde Detox",
        "descripcion": "Espinaca, pepino, piña, apio, limón y jengibre.",
        "categoria": "bebida", "precio": 55.0,
        "tiempo_preparacion": 4, "nivel_picante": 0,
    },

    # ── POSTRES (8) ─────────────────────────────────────────────────────────
    {
        "nombre": "Churros con Cajeta",
        "descripcion": "Churros fritos con azúcar y canela, dip de cajeta de cabra.",
        "categoria": "postre", "precio": 75.0,
        "tiempo_preparacion": 10, "nivel_picante": 0,
        "alergenos": ["gluten", "lacteos"],
    },
    {
        "nombre": "Flan Napolitano",
        "descripcion": "Flan casero con caramelo, queso crema y leche condensada.",
        "categoria": "postre", "precio": 65.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
        "alergenos": ["lacteos", "huevo"],
    },
    {
        "nombre": "Pay de Limón",
        "descripcion": "Pay de limón con base de galleta y merengue tatemado.",
        "categoria": "postre", "precio": 70.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
        "alergenos": ["gluten", "lacteos", "huevo"],
    },
    {
        "nombre": "Pastel Tres Leches",
        "descripcion": "Bizcocho esponjoso bañado en tres leches, cubierto de crema chantilly.",
        "categoria": "postre", "precio": 80.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
        "alergenos": ["gluten", "lacteos", "huevo"],
    },
    {
        "nombre": "Helado Artesanal",
        "descripcion": "2 bolas de helado artesanal: vainilla, chocolate, fresa o guanábana.",
        "categoria": "postre", "precio": 55.0,
        "tiempo_preparacion": 3, "nivel_picante": 0,
        "alergenos": ["lacteos"],
    },
    {
        "nombre": "Arroz con Leche",
        "descripcion": "Arroz cremoso con leche entera, canela, pasas y coco rallado.",
        "categoria": "postre", "precio": 55.0,
        "tiempo_preparacion": 5, "nivel_picante": 0,
        "alergenos": ["lacteos"],
    },
    {
        "nombre": "Volcán de Chocolate",
        "descripcion": "Pastelito tibio con centro fundido, helado de vainilla y fresas.",
        "categoria": "postre", "precio": 90.0,
        "tiempo_preparacion": 12, "nivel_picante": 0,
        "alergenos": ["gluten", "lacteos", "huevo"],
    },
    {
        "nombre": "Buñuelos con Piloncillo",
        "descripcion": "Buñuelos crujientes con miel de piloncillo, guayaba y canela.",
        "categoria": "postre", "precio": 65.0,
        "tiempo_preparacion": 10, "nivel_picante": 0,
        "alergenos": ["gluten"],
    },

    # ── ESPECIALES (7) ──────────────────────────────────────────────────────
    {
        "nombre": "Parrillada para 2",
        "descripcion": "Arrachera, costilla, chorizo, nopales, cebollitas, tortillas y dos salsas.",
        "categoria": "especial", "precio": 390.0,
        "tiempo_preparacion": 30, "nivel_picante": 0,
    },
    {
        "nombre": "Combo Familiar (10 tacos)",
        "descripcion": "10 tacos surtidos al pastor, tinga y canasta + 4 refrescos de vidrio.",
        "categoria": "especial", "precio": 330.0,
        "tiempo_preparacion": 15, "nivel_picante": 1,
    },
    {
        "nombre": "Menú del Día",
        "descripcion": "Sopa del día + plato fuerte + agua fresca + postre sencillo.",
        "categoria": "especial", "precio": 110.0,
        "tiempo_preparacion": 15, "nivel_picante": 0,
    },
    {
        "nombre": "Mole Poblano con Arroz",
        "descripcion": "Pierna de pollo en mole negro con 30 ingredientes, arroz y frijoles.",
        "categoria": "especial", "precio": 170.0,
        "tiempo_preparacion": 20, "nivel_picante": 1,
    },
    {
        "nombre": "Cochinita Pibil",
        "descripcion": "Cerdo marinado en achiote, horneado en hoja de plátano. Con cebolla morada.",
        "categoria": "especial", "precio": 150.0,
        "tiempo_preparacion": 15, "nivel_picante": 1,
    },
    {
        "nombre": "Chile en Nogada",
        "descripcion": "Chile poblano relleno de picadillo, cubierto de nogada, granada y perejil.",
        "categoria": "especial", "precio": 180.0,
        "tiempo_preparacion": 25, "nivel_picante": 1,
    },
    {
        "nombre": "Caldo de Piedra",
        "descripcion": "Caldo oaxaqueño con camarones, pescado y hierbas, preparado con piedras calientes.",
        "categoria": "especial", "precio": 195.0,
        "tiempo_preparacion": 20, "nivel_picante": 1,
        "alergenos": ["mariscos", "pescado"],
    },
]


def seed_menu(reset=False):
    col   = db["platillos"]
    ahora = datetime.utcnow()

    if reset:
        deleted = col.delete_many({}).deleted_count
        print(f"  Eliminados: {deleted} platillos previos")

    insertados = 0
    omitidos   = 0

    for p in PLATILLOS:
        img_file = _IMG.get(p["nombre"]) or _CAT_IMG.get(p["categoria"], "guacamole.jpg")
        img_path = BASE_IMG + img_file
        doc = {
            "nombre":               p["nombre"],
            "descripcion":          p.get("descripcion", ""),
            "categoria":            p["categoria"],
            "precio":               float(p["precio"]),
            "imagen":               img_path,
            "imagen_url":           img_path,
            "disponible":           True,
            "tiempo_preparacion":   p.get("tiempo_preparacion", 15),
            "nivel_picante":        p.get("nivel_picante", 0),
            "alergenos":            p.get("alergenos", []),
            "notas":                "",
            "fecha_creacion":       ahora,
            "fecha_actualizacion":  ahora,
        }
        if col.find_one({"nombre": p["nombre"]}):
            omitidos += 1
        else:
            col.insert_one(doc)
            insertados += 1

    total = col.count_documents({"disponible": True})
    print(f"  Insertados: {insertados}  |  Ya existían: {omitidos}  |  Total disponibles: {total}")

    # Resumen por categoría
    for slug, nombre in [("entrada","Entradas"),("plato_fuerte","Platos fuertes"),
                          ("bebida","Bebidas"),("postre","Postres"),("especial","Especiales")]:
        n = col.count_documents({"categoria": slug, "disponible": True})
        print(f"    {nombre}: {n}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed menú Callejón 9 — 52 platillos")
    parser.add_argument("--reset", action="store_true", help="Borrar platillos existentes antes de insertar")
    args = parser.parse_args()

    print("\nActualizando menú...")
    seed_menu(reset=args.reset)
    print("Done.\n")
