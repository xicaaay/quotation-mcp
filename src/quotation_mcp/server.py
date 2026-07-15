"""Punto de entrada del servidor MCP de cotizaciones."""

from fastmcp import FastMCP

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


def main() -> None:
    """Inicia el servidor utilizando el transporte configurado por FastMCP."""

    mcp.run()


if __name__ == "__main__":
    main()
