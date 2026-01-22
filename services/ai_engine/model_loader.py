from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_PATH = Path(__file__).parent / "../../services/trained_model"
MODEL_PATH = MODEL_PATH.resolve()

def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH, local_files_only=True)
    return tokenizer, model
