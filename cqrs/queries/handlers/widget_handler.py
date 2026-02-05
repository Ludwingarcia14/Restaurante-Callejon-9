# cqrs/queries/handlers/widget_handler.py

import time
import requests
from datetime import datetime
import os 

class WidgetQueryHandler:
    # Mover la configuración de caché y API Key aquí
    FMP_API_KEY = os.environ.get("FMP_API_KEY", "5AFEm8X6Xfv5b6xQ8DhHQB5diALaK82T")
    CACHE_BOLSA_SEGUNDOS = 900 
    CACHE_DIVISAS_SEGUNDOS = 3600 

    # La caché debe ser compartida (variable de clase)
    cache_app = {
        "bolsa": {"data": None, "last_updated": 0},
        "divisas": {"data": None, "last_updated": 0}
    }

    @classmethod
    def get_divisas_data(cls):
        """Obtiene datos de divisas con caché."""
        ahora = time.time()
        cache_data = cls.cache_app["divisas"]
        cache_valida = (ahora - cache_data["last_updated"]) < cls.CACHE_DIVISAS_SEGUNDOS

        if cache_valida and cache_data["data"] is not None:
            return cache_data["data"]

        try:
            response = requests.get("https://api.exchangerate.host/latest?base=USD", timeout=30)
            response.raise_for_status()
            data = response.json()

            rates = {"EUR": data["rates"].get("EUR", 0), "MXN": data["rates"].get("MXN", 0)}
            result = {"rates": rates, "date": data.get("date", "")}

            cache_data["data"] = result
            cache_data["last_updated"] = ahora
            return result
        except Exception as e:
            fallback = {"rates": {"EUR": 0.93, "MXN": 18.50}, "date": datetime.now().strftime("%Y-%m-%d")}
            cache_data["data"] = fallback
            cache_data["last_updated"] = ahora 
            return fallback

    @classmethod
    def get_bolsa_data(cls):
        """Obtiene datos de bolsa con caché."""
        ahora = time.time()
        cache_data = cls.cache_app["bolsa"]
        cache_valida = (ahora - cache_data["last_updated"]) < cls.CACHE_BOLSA_SEGUNDOS

        if cache_valida and cache_data["data"] is not None:
            return cache_data["data"]
            
        try:
            symbols = "^GSPC,^IXIC,^DJI"
            url = f"https://financialmodelingprep.com/api/v3/quote/{symbols}?apikey={cls.FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            cache_data["data"] = data
            cache_data["last_updated"] = ahora
            return data
        except Exception as e:
            fallback = [
                {"symbol": "^GSPC", "price": 4500, "change": 12, "changesPercentage": 0.27},
                {"symbol": "^IXIC", "price": 15000, "change": -45, "changesPercentage": -0.30},
                {"symbol": "^DJI", "price": 35000, "change": 80, "changesPercentage": 0.23}
            ]
            cache_data["data"] = fallback
            cache_data["last_updated"] = ahora
            return fallback