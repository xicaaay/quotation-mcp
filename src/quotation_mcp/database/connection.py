"""Acceso controlado a PostgreSQL para operaciones de solo lectura."""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from quotation_mcp.config import get_settings


@contextmanager
def get_read_connection() -> Iterator[Connection]:
    """Abre una conexión y fuerza una transacción de solo lectura.

    Aunque las consultas del repositorio son SELECT, esta protección adicional
    evita escrituras accidentales si en el futuro se introduce SQL incorrecto.
    """

    settings = get_settings()
    connection = psycopg.connect(
        settings.database_url,
        connect_timeout=settings.database_connect_timeout,
        row_factory=dict_row,
        autocommit=False,
    )

    try:
        connection.execute("SET TRANSACTION READ ONLY")
        yield connection
        connection.rollback()
    finally:
        connection.close()
