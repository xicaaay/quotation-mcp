"""Interpretación de consultas vagas y ordenamiento de resultados."""

import re
import unicodedata
from decimal import Decimal
from typing import Any

from rapidfuzz import fuzz

from quotation_mcp.config import get_settings
from quotation_mcp.models.product import ProductFilters
from quotation_mcp.repositories.product_repository import ProductRepository


_SYNONYMS: dict[str, tuple[str, ...]] = {
    "web": ("sitio web", "pagina web", "landing", "tienda en linea", "ecommerce"),
    "pagina": ("pagina web", "landing page", "sitio web"),
    "redes": ("redes sociales", "publicacion", "contenido", "post"),
    "ia": ("inteligencia artificial", "ai"),
    "video": ("video", "audiovisual"),
    "imagen": ("imagenes", "grafica", "diseno"),
    "marca": ("identidad visual", "logotipo", "branding"),
    "presentacion": ("diapositivas", "presentacion comercial"),
    "soporte": ("mantenimiento", "horas", "acompanamiento tecnico"),
    "mensual": ("monthly", "recurrente", "mes"),
    "chat": ("chatbot", "bot"),
    "api": ("integracion", "api externa"),
}


class ProductSearchService:
    """Servicio que traduce lenguaje natural a búsquedas del catálogo."""

    def __init__(self, repository: ProductRepository | None = None) -> None:
        self.repository = repository or ProductRepository()

    @staticmethod
    def normalize(value: str) -> str:
        """Normaliza acentos, mayúsculas y espacios para comparar textos."""

        decomposed = unicodedata.normalize("NFKD", value)
        without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
        return re.sub(r"\s+", " ", without_accents.lower()).strip()

    def expand_query(self, query: str) -> str:
        """Agrega términos relacionados para mejorar solicitudes poco precisas."""

        normalized = self.normalize(query)
        expanded = [normalized]
        for trigger, related_terms in _SYNONYMS.items():
            if trigger in normalized:
                expanded.extend(related_terms)
        return " ".join(dict.fromkeys(expanded))

    def infer_filters(self, query: str, provided: ProductFilters) -> ProductFilters:
        """Infiere filtros obvios sin reemplazar los enviados explícitamente."""

        text = self.normalize(query)
        values = provided.model_dump()

        if values["area"] is None:
            if any(term in text for term in ("diseno", "grafico", "marca", "redes", "imagen", "presentacion")):
                values["area"] = "DESIGN"
            elif any(term in text for term in ("desarrollo", "web", "api", "chatbot", "tienda", "soporte")):
                values["area"] = "DEVELOPMENT"

        if values["pricing_type"] is None and any(
            term in text for term in ("mensual", "recurrente", "cada mes")
        ):
            values["pricing_type"] = "RECURRING"

        if values["billing_period"] is None and "mensual" in text:
            values["billing_period"] = "MONTHLY"

        # Detecta expresiones frecuentes como "menos de 700" o "hasta 500".
        if values["max_price"] is None:
            match = re.search(r"(?:menos de|hasta|maximo|max)\s*\$?\s*(\d+(?:\.\d+)?)", text)
            if match:
                values["max_price"] = Decimal(match.group(1))

        if values["min_price"] is None:
            match = re.search(r"(?:mas de|desde|minimo|min)\s*\$?\s*(\d+(?:\.\d+)?)", text)
            if match:
                values["min_price"] = Decimal(match.group(1))

        return ProductFilters(**values)

    def search(
        self,
        query: str,
        filters: ProductFilters,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Busca productos con recuperación amplia y ranking difuso."""

        settings = get_settings()
        effective_limit = min(limit or 10, settings.max_results)
        inferred_filters = self.infer_filters(query, filters)
        expanded_query = self.expand_query(query)
        candidates = self.repository.search_candidates(expanded_query, inferred_filters)

        normalized_query = self.normalize(expanded_query)
        ranked: list[tuple[float, dict[str, Any]]] = []
        for product in candidates:
            searchable = self.normalize(
                " ".join(
                    filter(
                        None,
                        [product["code"], product["name"], product["description"], product["unit_name"]],
                    )
                )
            )
            score = max(
                fuzz.token_set_ratio(normalized_query, searchable),
                fuzz.partial_ratio(normalized_query, searchable),
            )
            ranked.append((float(score), product))

        ranked.sort(key=lambda item: (-item[0], item[1]["display_order"], item[1]["name"]))
        results = [dict(product, relevance_score=round(score, 2)) for score, product in ranked[:effective_limit]]

        return {
            "query": query,
            "expanded_query": expanded_query,
            "applied_filters": inferred_filters.model_dump(mode="json"),
            "total_results": len(results),
            "results": results,
            "refinement_hint": (
                "Para profundizar, llama read_refine_product_search enviando original_query, "
                "refinement y, si aplica, filtros adicionales."
            ),
        }
