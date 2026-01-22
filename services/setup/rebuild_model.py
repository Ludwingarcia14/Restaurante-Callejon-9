from transformers import AutoTokenizer, AutoConfig, AutoModelForSeq2SeqLM # <-- ¡IMPORTAR EL MODELO!
from pathlib import Path

# Modelo base
BASE_MODEL = "t5-small"

# Carpeta del modelo entrenado
# La ruta relativa es correcta: d:\Proyectos\python\pyme\services\setup
# Subir dos niveles (..) y entrar a services/trained_model
MODEL_DIR = Path(__file__).parent / "../../services/trained_model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Ruta de destino: {MODEL_DIR.resolve()}")

# 1. Cargar el Modelo COMPLETO (incluye los pesos)
print(f"⏳ Descargando el modelo completo '{BASE_MODEL}'...")
try:
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)
    print("✅ Modelo descargado exitosamente.")
except Exception as e:
    print(f"❌ Error al descargar el modelo: {e}. ¿Revisó su conexión a internet?")
    exit()

# 2. Guardar el Tokenizer
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
tokenizer.save_pretrained(MODEL_DIR)
print("✅ Tokenizer guardado.")

# 3. Guardar la Configuración
# La configuración ya viene con el modelo, pero se puede guardar por separado:
model.config.save_pretrained(MODEL_DIR)
print("✅ Config.json guardado.")

# 4. Guardar los Pesos del Modelo (Crea pytorch_model.bin)
model.save_pretrained(MODEL_DIR)
print("✅ Pesos del modelo (pytorch_model.bin) guardados.")

print("\n🎉 Reconstrucción de modelo completada en la carpeta 'trained_model'.")