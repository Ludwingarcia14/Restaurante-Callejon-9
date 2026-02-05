from config.db import db

def poblar_menu():
    productos = [
        {"nombre": "Tacos al Pastor (5)", "precio": 95.0, "categoria": "Platillos", "estado": "activo"},
        {"nombre": "Enchiladas Suizas", "precio": 125.0, "categoria": "Platillos", "estado": "activo"},
        {"nombre": "Hamburguesa BBQ", "precio": 140.0, "categoria": "Platillos", "estado": "activo"},
        {"nombre": "Cerveza Corona", "precio": 45.0, "categoria": "Bebidas", "estado": "activo"},
        {"nombre": "Refresco de Vidrio", "precio": 30.0, "categoria": "Bebidas", "estado": "activo"},
        {"nombre": "Agua del Día", "precio": 35.0, "categoria": "Bebidas", "estado": "activo"},
        {"nombre": "Papas a la Francesa", "precio": 55.0, "categoria": "Complementos", "estado": "activo"},
        {"nombre": "Guacamole Extra", "precio": 25.0, "categoria": "Complementos", "estado": "activo"}
    ]
    # Limpiamos antes de insertar para no duplicar (opcional)
    db.productos.delete_many({}) 
    db.productos.insert_many(productos)
    print("✅ Menú actualizado con éxito.")

if __name__ == "__main__":
    poblar_menu()