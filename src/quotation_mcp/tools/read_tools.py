"""Herramientas MCP públicas. Todas respetan el prefijo read_."""

from decimal import Decimal
from typing import Any

from fastmcp import FastMCP

from quotation_mcp.config import get_settings
from quotation_mcp.models.product import ProductFilters
from quotation_mcp.repositories.product_repository import ProductRepository
from quotation_mcp.services.search_service import ProductSearchService


repository = ProductRepository()
search_service = ProductSearchService(repository)


def register_read_tools(mcp: FastMCP) -> None:
    """Registra únicamente herramientas que consultan información."""

    @mcp.tool
    def read_health_check() -> dict[str, Any]:
        """Verifica que el servidor MCP pueda leer la base de datos."""

        return {"service": "quotation-mcp", "status": "ok", **repository.health_check()}

    @mcp.tool
    def read_database_catalog() -> dict[str, Any]:
        """Describe las entidades y campos que este MCP puede consultar.

        Úsala cuando el agente necesite entender qué información está disponible
        antes de decidir qué otra herramienta ejecutar.
        """

        return {
            "mode": "read_only",
            "entities": {
                "products": {
                    "table": "dm_products",
                    "description": "Catálogo de productos y servicios cotizables.",
                    "fields": [
                        "id", "code", "name", "description", "area", "pricing_type",
                        "base_price", "currency", "unit_name", "billing_period",
                        "estimated_delivery_value", "estimated_delivery_unit",
                        "minimum_quantity", "is_active", "display_order",
                        "created_at", "updated_at",
                    ],
                    "areas": ["DESIGN", "DEVELOPMENT"],
                    "pricing_types": ["PER_UNIT", "FIXED", "RECURRING"],
                    "billing_periods": ["ONE_TIME", "MONTHLY", "QUARTERLY", "YEARLY"],
                    "delivery_units": ["BUSINESS_DAYS", "CALENDAR_DAYS", "WEEKS", "MONTHS"],
                }
            },
        }

    @mcp.tool
    def read_search_products(
        query: str,
        area: str | None = None,
        pricing_type: str | None = None,
        billing_period: str | None = None,
        active_only: bool = True,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        delivery_unit: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Busca productos usando una solicitud libre o vaga en español.

        Ejemplos: "algo para redes", "una web barata", "servicios mensuales",
        "productos de IA" o "diseño de marca por menos de 1000".
        """

        filters = ProductFilters(
            area=area,
            pricing_type=pricing_type,
            billing_period=billing_period,
            active_only=active_only,
            min_price=min_price,
            max_price=max_price,
            delivery_unit=delivery_unit,
        )
        return search_service.search(query=query, filters=filters, limit=limit)

    @mcp.tool
    def read_refine_product_search(
        original_query: str,
        refinement: str,
        area: str | None = None,
        pricing_type: str | None = None,
        billing_period: str | None = None,
        active_only: bool = True,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        delivery_unit: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Profundiza una búsqueda previa combinándola con una nueva condición.

        Debe recibir la consulta anterior y la aclaración actual. Ejemplo:
        original_query="algo para redes" y refinement="solo paquetes hasta 600".
        """

        combined_query = f"{original_query}. Aclaración adicional: {refinement}"
        filters = ProductFilters(
            area=area,
            pricing_type=pricing_type,
            billing_period=billing_period,
            active_only=active_only,
            min_price=min_price,
            max_price=max_price,
            delivery_unit=delivery_unit,
        )
        response = search_service.search(combined_query, filters, limit)
        response["original_query"] = original_query
        response["refinement"] = refinement
        return response

    @mcp.tool
    def read_list_products(
        area: str | None = None,
        pricing_type: str | None = None,
        billing_period: str | None = None,
        active_only: bool = True,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        delivery_unit: str | None = None,
        limit: int = 25,
    ) -> dict[str, Any]:
        """Lista productos mediante filtros exactos, sin búsqueda textual."""

        settings = get_settings()
        filters = ProductFilters(
            area=area,
            pricing_type=pricing_type,
            billing_period=billing_period,
            active_only=active_only,
            min_price=min_price,
            max_price=max_price,
            delivery_unit=delivery_unit,
        )
        products = repository.list_products(filters, min(limit, settings.max_results))
        return {
            "applied_filters": filters.model_dump(mode="json"),
            "total_results": len(products),
            "results": products,
        }

    @mcp.tool
    def read_product_detail(identifier: str) -> dict[str, Any]:
        """Obtiene un producto por UUID, código o nombre comercial exacto."""

        product = repository.get_by_identifier(identifier)
        if product is None:
            return {
                "found": False,
                "identifier": identifier,
                "message": "No se encontró un producto exacto. Usa read_search_products para una búsqueda flexible.",
            }
        return {"found": True, "product": product}

    @mcp.tool
    def read_compare_products(identifiers: list[str]) -> dict[str, Any]:
        """Compara varios productos identificados por UUID, código o nombre exacto."""

        products = repository.get_many_by_identifiers(identifiers)
        found_keys = {
            value.lower()
            for product in products
            for value in (product["id"], product["code"], product["name"])
        }
        missing = [value for value in identifiers if value.strip().lower() not in found_keys]
        return {
            "requested": identifiers,
            "total_found": len(products),
            "missing_identifiers": missing,
            "products": products,
        }
