import os
import json
import re
import logging

logger = logging.getLogger(__name__)


class IARecomendacionService:
    """
    Genera recomendaciones por cluster usando Claude API si ANTHROPIC_API_KEY está
    configurada, o reglas inteligentes basadas en los datos reales del cluster.
    """

    @staticmethod
    def generar_recomendaciones_kmeans(resumen: list, evaluacion: dict) -> list:
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if api_key:
            try:
                return IARecomendacionService._via_claude(resumen, evaluacion, api_key)
            except Exception as e:
                logger.warning("Claude API falló, usando reglas: %s", e)
        return IARecomendacionService._via_reglas(resumen)

    # ── Claude ────────────────────────────────────────────────────────────────
    @staticmethod
    def _via_claude(resumen, evaluacion, api_key):
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        lineas = []
        for c in resumen:
            sil = c.get("silhouette")
            sil_txt = f", índice de silueta={sil:.3f}" if sil is not None else ""
            lineas.append(
                f"- {c['label']}: {c['num_mesas']} mesas, "
                f"ticket promedio ${c['ticket_prom']:.2f}, "
                f"{c['visitas_prom']:.1f} visitas/mes{sil_txt}"
            )

        sil_global = evaluacion.get("silhouette_score")
        contexto = "\n".join(lineas)
        if sil_global is not None:
            contexto += f"\nSilhouette global del modelo: {sil_global:.3f}"

        prompt = (
            "Eres un consultor senior de restaurantes. "
            "Analiza los clusters de mesas detectados por K-Means y genera una recomendación "
            "específica, accionable y en español (máximo 2 oraciones) para cada cluster. "
            "Usa los números reales (ticket, frecuencia) en tu respuesta. "
            "Responde ÚNICAMENTE con un arreglo JSON con la estructura: "
            '[{"cluster": "<nombre>", "recomendacion": "<texto>"}]. '
            "Sin texto adicional, sin markdown.\n\n"
            f"Datos del restaurante:\n{contexto}"
        )

        respuesta = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = respuesta.content[0].text.strip()
        if not raw.startswith("["):
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if not match:
                raise ValueError("Respuesta de Claude sin JSON válido")
            raw = match.group()

        data = json.loads(raw)
        rec_map = {item["cluster"]: item["recomendacion"] for item in data}
        return [rec_map.get(c["label"], IARecomendacionService._regla(c)) for c in resumen]

    # ── Reglas inteligentes ────────────────────────────────────────────────────
    @staticmethod
    def _via_reglas(resumen):
        return [IARecomendacionService._regla(c) for c in resumen]

    @staticmethod
    def _regla(c):
        label   = c["label"]
        ticket  = c["ticket_prom"]
        visitas = c["visitas_prom"]
        n       = c["num_mesas"]

        if "VIP" in label:
            if ticket >= 400:
                return (
                    f"Tus {n} mesa(s) VIP generan un ticket de ${ticket:.0f} con {visitas:.0f} visitas — "
                    "son el núcleo de ingresos del turno. "
                    "Asigna siempre a tu mesero más experimentado y considera un menú degustación exclusivo para este segmento."
                )
            return (
                f"Las {n} mesa(s) VIP tienen {visitas:.0f} visitas con ${ticket:.0f} de ticket. "
                "Implementa una tarjeta de cliente frecuente o postre de cortesía en la tercera visita "
                "para consolidar su fidelidad y elevar el ticket promedio."
            )

        if "Regular" in label:
            if visitas >= 4:
                return (
                    f"Las {n} mesas regulares son el segmento más estable con {visitas:.1f} visitas y ${ticket:.0f} de ticket. "
                    "Mantén consistencia en tiempos de servicio y sugiere activamente complementos (bebida, postre) "
                    "para migrarlas al segmento VIP."
                )
            return (
                f"Las {n} mesas regulares visitan {visitas:.1f} veces con ${ticket:.0f} de ticket — "
                "hay margen de crecimiento. "
                "Ofrece una promoción de 2x1 en bebidas o una entrada de bienvenida para aumentar su frecuencia."
            )

        # Ocasionales
        if n >= 4:
            return (
                f"Las {n} mesas ocasionales representan baja ocupación ({visitas:.1f} visitas, ${ticket:.0f}). "
                "Analiza si su ubicación en el salón es un factor — reubicarlas cerca de la barra o ventana "
                "puede incrementar su demanda significativamente."
            )
        return (
            f"Con {n} mesa(s) ocasional(es) y ${ticket:.0f} de ticket, evalúa si el horario de asignación es el problema. "
            "Un menú de mediodía o set lunch puede activar su uso en momentos de baja ocupación."
        )
