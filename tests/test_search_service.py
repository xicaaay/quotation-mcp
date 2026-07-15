"""Pruebas unitarias para la interpretación de búsquedas vagas."""

from quotation_mcp.models.product import ProductFilters
from quotation_mcp.services.search_service import ProductSearchService


class FakeRepository:
    """Repositorio mínimo que evita depender de PostgreSQL durante la prueba."""

    def search_candidates(self, query_text, filters, candidate_limit=200):
        return [
            {
                "id": "1",
                "code": "DEV_LANDING_PAGE",
                "name": "Landing page",
                "description": "Página responsive para campañas.",
                "area": "DEVELOPMENT",
                "pricing_type": "FIXED",
                "base_price": 650,
                "currency": "USD",
                "unit_name": "landing page",
                "billing_period": "ONE_TIME",
                "estimated_delivery_value": 2,
                "estimated_delivery_unit": "WEEKS",
                "minimum_quantity": 1,
                "is_active": True,
                "display_order": 80,
                "created_at": None,
                "updated_at": None,
            }
        ]


def test_infers_development_and_max_price():
    service = ProductSearchService(FakeRepository())
    filters = service.infer_filters("Necesito una web hasta 700", ProductFilters())

    assert filters.area == "DEVELOPMENT"
    assert filters.max_price == 700


def test_expands_ai_term():
    service = ProductSearchService(FakeRepository())

    assert "inteligencia artificial" in service.expand_query("video con IA")
