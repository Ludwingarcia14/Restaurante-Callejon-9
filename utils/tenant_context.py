"""
Contexto de tenant por request/tarea.

Mantiene el identificador del restaurante (tenant) activo durante el ciclo de
vida de una peticion o de una tarea en segundo plano. Se usa `contextvars` para
que funcione tanto en peticiones HTTP como en hilos/jobs, y para que sea
testeable sin depender de Flask ni de Mongo.
"""
from contextvars import ContextVar
from typing import Optional

_current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)


class NoTenantContextError(RuntimeError):
    """Se intento acceder a datos sin un tenant activo (fail-closed)."""


def set_current_tenant(tenant_id: Optional[str]) -> None:
    _current_tenant.set(tenant_id)


def get_current_tenant() -> Optional[str]:
    return _current_tenant.get()


def require_current_tenant() -> str:
    tenant_id = _current_tenant.get()
    if not tenant_id:
        raise NoTenantContextError(
            "No hay un tenant activo en el contexto. "
            "El acceso a datos requiere un restaurante identificado."
        )
    return tenant_id
