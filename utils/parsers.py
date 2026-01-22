import re

def limpiar_moneda(texto):
    """Convierte '$100 mil', '2 MDP' a float."""
    if not texto or not isinstance(texto, str):
        return 0.0

    clean = texto.lower().replace(',', '').replace('$', '').strip()
    multiplicador = 1

    if 'mdp' in clean or 'millones' in clean:
        multiplicador = 1000000
        clean = re.sub(r'(mdp|millones)', '', clean)
    elif 'mil' in clean or 'k' in clean:
        multiplicador = 1000
        clean = re.sub(r'(mil|k)', '', clean)

    match = re.search(r"(\d+(.\d+)?)", clean)
    if match:
        return float(match.group(1)) * multiplicador
    return 0.0

def parsear_rango_moneda(texto):
    """Input: '$200,000 a $20,000,000' -> Output: (200000.0, 20000000.0)"""
    if not texto: return (0, float('inf'))
    partes = re.split(r'\s+(?:a|hasta|-)\s+', texto.lower())
    min_val = limpiar_moneda(partes[0])
    max_val = limpiar_moneda(partes[1]) if len(partes) > 1 else float('inf')
    return (min_val, max_val)