"""Consultas SQL de solo lectura para el catálogo de productos."""

from decimal import Decimal
from typing import Any

from psycopg import sql

from quotation_mcp.database.connection import get_read_connection
from quotation_mcp.models.product import ProductFilters


_SELECT_FIELDS = """
    id::text AS id,
    code,
    name,
    description,
    area::text AS area,
    pricing_type::text AS pricing_type,
    base_price,
    currency,
    unit_name,
    billing_period::text AS billing_period,
    estimated_delivery_value,
    estimated_delivery_unit::text AS estimated_delivery_unit,
    minimum_quantity,
    is_active,
    display_order,
    created_at,
    updated_at
"""


class ProductRepository:
    """Repositorio especializado en lecturas de la tabla dm_products."""

    def health_check(self) -> dict[str, Any]:
        """Comprueba la conexión y obtiene un conteo básico del catálogo."""

        with get_read_connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*)::int AS total FROM dm_products"
            ).fetchone()
        return {"database": "ok", "total_products": row["total"]}

    def get_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        """Busca un producto por UUID, código o nombre exacto."""

        query = f"""
            SELECT {_SELECT_FIELDS}
            FROM dm_products
            WHERE id::text = %(identifier)s
               OR LOWER(code) = LOWER(%(identifier)s)
               OR LOWER(name) = LOWER(%(identifier)s)
            LIMIT 1
        """
        with get_read_connection() as connection:
            return connection.execute(query, {"identifier": identifier.strip()}).fetchone()

    def list_products(
        self,
        filters: ProductFilters,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Lista productos aplicando filtros validados y parámetros seguros."""

        clauses: list[sql.Composable] = []
        params: dict[str, Any] = {"limit": limit}

        if filters.active_only:
            clauses.append(sql.SQL("is_active = TRUE"))
        if filters.area:
            clauses.append(sql.SQL("area::text = %(area)s"))
            params["area"] = filters.area
        if filters.pricing_type:
            clauses.append(sql.SQL("pricing_type::text = %(pricing_type)s"))
            params["pricing_type"] = filters.pricing_type
        if filters.billing_period:
            clauses.append(sql.SQL("billing_period::text = %(billing_period)s"))
            params["billing_period"] = filters.billing_period
        if filters.delivery_unit:
            clauses.append(sql.SQL("estimated_delivery_unit::text = %(delivery_unit)s"))
            params["delivery_unit"] = filters.delivery_unit
        if filters.min_price is not None:
            clauses.append(sql.SQL("base_price >= %(min_price)s"))
            params["min_price"] = filters.min_price
        if filters.max_price is not None:
            clauses.append(sql.SQL("base_price <= %(max_price)s"))
            params["max_price"] = filters.max_price

        where_sql = sql.SQL(" AND ").join(clauses) if clauses else sql.SQL("TRUE")
        query = sql.SQL(
            f"""
            SELECT {_SELECT_FIELDS}
            FROM dm_products
            WHERE {{where_sql}}
            ORDER BY display_order ASC, name ASC
            LIMIT %(limit)s
            """
        ).format(where_sql=where_sql)

        with get_read_connection() as connection:
            return list(connection.execute(query, params).fetchall())

    def search_candidates(
        self,
        query_text: str,
        filters: ProductFilters,
        candidate_limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Obtiene candidatos mediante coincidencias parciales en campos textuales."""

        words = [word for word in query_text.split() if len(word) >= 2]
        params: dict[str, Any] = {
            "query": f"%{query_text}%",
            "candidate_limit": candidate_limit,
        }
        clauses = [
            "(code ILIKE %(query)s OR name ILIKE %(query)s OR COALESCE(description, '') ILIKE %(query)s OR unit_name ILIKE %(query)s)"
        ]

        # Una consulta vaga puede contener varias palabras no consecutivas.
        # Se agrega una condición OR por palabra para ampliar la recuperación.
        for index, word in enumerate(words[:10]):
            key = f"word_{index}"
            params[key] = f"%{word}%"
            clauses.append(
                f"(code ILIKE %({key})s OR name ILIKE %({key})s OR COALESCE(description, '') ILIKE %({key})s OR unit_name ILIKE %({key})s)"
            )

        filter_clauses: list[str] = []
        if filters.active_only:
            filter_clauses.append("is_active = TRUE")
        for field, column in (
            (filters.area, "area::text"),
            (filters.pricing_type, "pricing_type::text"),
            (filters.billing_period, "billing_period::text"),
            (filters.delivery_unit, "estimated_delivery_unit::text"),
        ):
            if field:
                parameter = column.split("::")[0]
                filter_clauses.append(f"{column} = %({parameter})s")
                params[parameter] = field
        if filters.min_price is not None:
            filter_clauses.append("base_price >= %(min_price)s")
            params["min_price"] = filters.min_price
        if filters.max_price is not None:
            filter_clauses.append("base_price <= %(max_price)s")
            params["max_price"] = filters.max_price

        text_where = " OR ".join(clauses)
        filters_where = " AND ".join(filter_clauses) or "TRUE"
        sql_query = f"""
            SELECT {_SELECT_FIELDS}
            FROM dm_products
            WHERE ({text_where}) AND ({filters_where})
            ORDER BY display_order ASC, name ASC
            LIMIT %(candidate_limit)s
        """

        with get_read_connection() as connection:
            return list(connection.execute(sql_query, params).fetchall())

    def get_many_by_identifiers(self, identifiers: list[str]) -> list[dict[str, Any]]:
        """Recupera varios productos por código, nombre o UUID."""

        cleaned = [value.strip() for value in identifiers if value.strip()]
        if not cleaned:
            return []

        query = f"""
            SELECT {_SELECT_FIELDS}
            FROM dm_products
            WHERE id::text = ANY(%(identifiers)s)
               OR LOWER(code) = ANY(%(lower_identifiers)s)
               OR LOWER(name) = ANY(%(lower_identifiers)s)
            ORDER BY display_order ASC, name ASC
        """
        with get_read_connection() as connection:
            return list(
                connection.execute(
                    query,
                    {
                        "identifiers": cleaned,
                        "lower_identifiers": [value.lower() for value in cleaned],
                    },
                ).fetchall()
            )
