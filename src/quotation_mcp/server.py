"""Servidor principal del MCP de cotizaciones."""

from fastmcp import FastMCP


mcp = FastMCP(
    name="Quotation MCP",
)


@mcp.tool
def health_check() -> dict[str, str]:
    """Comprueba que el servidor MCP esté funcionando correctamente."""

    return {
        "status": "ok",
        "service": "quotation-mcp",
    }


def main() -> None:
    """Inicia el servidor MCP."""

    mcp.run()


if __name__ == "__main__":
    main()