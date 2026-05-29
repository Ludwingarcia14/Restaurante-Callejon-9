from flask import jsonify
from bson import ObjectId
from datetime import datetime


def api_ok(data=None, message=None, code=200):
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload.update(data) if isinstance(data, dict) else payload.__setitem__("data", data)
    return jsonify(payload), code


def api_error(message="Error interno del servidor", code=500):
    return jsonify({"success": False, "message": message}), code


def serialize_doc(doc):
    """Convierte ObjectId y datetime a tipos JSON-serializables en un documento MongoDB."""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        elif isinstance(value, list):
            result[key] = [serialize_doc(i) if isinstance(i, dict) else i for i in value]
        elif isinstance(value, dict):
            result[key] = serialize_doc(value)
        else:
            result[key] = value
    return result


def serialize_docs(docs):
    """Aplica serialize_doc a una lista de documentos."""
    return [serialize_doc(d) for d in docs]
