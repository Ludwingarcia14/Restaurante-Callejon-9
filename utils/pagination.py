"""
Helper de paginación para endpoints de lista.
Uso:
    limit, page, skip = get_pagination_params()
    data = list(collection.find(query).skip(skip).limit(limit))
    total = collection.count_documents(query)
    return jsonify(paginate_response(data, total, page, limit))
"""
from flask import request


def get_pagination_params(default_limit: int = 20, max_limit: int = 100):
    """
    Lee ?page=N&limit=N de la query string.
    Retorna (limit, page, skip).
    """
    try:
        limit = int(request.args.get("limit", default_limit))
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        limit, page = default_limit, 1

    limit = min(max(limit, 1), max_limit)
    page = max(page, 1)
    skip = (page - 1) * limit
    return limit, page, skip


def paginate_response(data: list, total: int, page: int, limit: int) -> dict:
    total_pages = max((total + limit - 1) // limit, 1)
    return {
        "data": data,
        "pagination": {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    }
