"""Punto de entrada HTTP del servidor MCP de cotizaciones."""

from datetime import UTC, datetime
from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from quotation_mcp.config import get_settings
from quotation_mcp.tools.read_tools import register_read_tools


mcp = FastMCP(
    name="Quotation MCP Read",
    instructions=(
        "Servidor de solo lectura para consultar productos y servicios cotizables. "
        "Todas las herramientas públicas comienzan con read_. Para solicitudes vagas, "
        "utiliza read_search_products. Para profundizar una consulta previa, utiliza "
        "read_refine_product_search e incluye la consulta original."
    ),
)

register_read_tools(mcp)


@mcp.custom_route("/", methods=["GET"])
async def service_info(_: Request) -> JSONResponse:
    """Expone información pública mínima para comprobar el despliegue."""

    settings = get_settings()
    payload: dict[str, Any] = {
        "service": "quotation-mcp",
        "status": "running",
        "transport": "streamable-http",
        "mcp_endpoint": settings.normalized_mcp_path,
        "health_endpoint": "/health",
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return JSONResponse(payload)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    """Health check ligero utilizado por Railway."""

    return JSONResponse(
        {
            "service": "quotation-mcp",
            "status": "ok",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def main() -> None:
    """Inicia FastMCP mediante Streamable HTTP para Railway."""

    settings = get_settings()
    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port,
        path=settings.normalized_mcp_path,
    )


if __name__ == "__main__":
    main()
