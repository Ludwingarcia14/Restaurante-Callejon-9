"""
Tests del aislamiento multi-tenant en BaseModel.

Se usa una coleccion falsa (no Mongo) porque BaseModel no debe depender de la
base de datos: cada subclase inyecta su `collection`. Asi la logica critica de
scoping por tenant se prueba sin conexion a Mongo.
"""
import types
import pytest

from models.base_model import BaseModel
from utils.tenant_context import (
    set_current_tenant,
    NoTenantContextError,
)


class FakeCursor:
    def __init__(self, docs):
        self._docs = docs

    def sort(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    """Captura los argumentos con que BaseModel llama a Mongo."""

    def __init__(self, find_result=None, find_one_result=None):
        self.last_find_filter = None
        self.last_find_one_filter = None
        self.last_insert_doc = None
        self._find_result = find_result or []
        self._find_one_result = find_one_result

    def find(self, filtro=None):
        self.last_find_filter = filtro
        return FakeCursor(self._find_result)

    def find_one(self, filtro=None):
        self.last_find_one_filter = filtro
        return self._find_one_result

    def insert_one(self, doc):
        self.last_insert_doc = doc
        return types.SimpleNamespace(inserted_id="fake_id")


@pytest.fixture(autouse=True)
def _reset_tenant():
    """Limpia el contexto de tenant antes y despues de cada test."""
    set_current_tenant(None)
    yield
    set_current_tenant(None)


def _make_model(collection):
    class _Model(BaseModel):
        pass
    _Model.collection = collection
    return _Model


def test_find_all_scopes_query_by_current_tenant():
    coll = FakeCollection(find_result=[{"_id": 1}])
    Model = _make_model(coll)

    set_current_tenant("fonda_1")
    Model.find_all({"estado": "pendiente"})

    assert coll.last_find_filter == {"estado": "pendiente", "tenant_id": "fonda_1"}


def test_find_all_without_tenant_raises_and_does_not_query():
    coll = FakeCollection()
    Model = _make_model(coll)

    # Sin tenant activo (el fixture lo limpia a None)
    with pytest.raises(NoTenantContextError):
        Model.find_all({"estado": "pendiente"})

    assert coll.last_find_filter is None  # nunca toco la coleccion


def test_create_stamps_tenant_id_on_document():
    coll = FakeCollection()
    Model = _make_model(coll)

    set_current_tenant("fonda_1")
    Model.create({"total": 250})

    assert coll.last_insert_doc["tenant_id"] == "fonda_1"
    assert coll.last_insert_doc["total"] == 250


def test_find_by_id_scopes_by_tenant():
    coll = FakeCollection(find_one_result={"_id": "abc"})
    Model = _make_model(coll)

    set_current_tenant("fonda_1")
    Model.find_by_id("64b8f0000000000000000000")

    assert coll.last_find_one_filter["tenant_id"] == "fonda_1"
