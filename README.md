# Quotation MCP Read

Servidor MCP en Python para consultar el catálogo `dm_products` de PostgreSQL. Esta implementación es de solo lectura y utiliza Streamable HTTP para despliegues remotos.

## Herramientas expuestas

- `read_health_check`: valida conexión y conteo de productos.
- `read_database_catalog`: describe la entidad y campos disponibles.
- `read_search_products`: interpreta búsquedas libres o vagas.
- `read_refine_product_search`: profundiza una consulta anterior.
- `read_list_products`: aplica filtros exactos.
- `read_product_detail`: busca por UUID, código o nombre exacto.
- `read_compare_products`: compara varios productos.

## Ejecución local

```bash
cp .env.example .env
uv sync
uv run quotation-mcp
```

Rutas locales:

- MCP: `http://localhost:8000/mcp`
- Estado: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`

## Despliegue en Railway

1. Sube el proyecto a GitHub.
2. En Railway, crea un servicio desde el repositorio.
3. Configura `DATABASE_URL` en **Variables**.
4. Genera un dominio público en **Networking**.
5. Railway construirá el `Dockerfile` y comprobará `/health`.

No es necesario crear manualmente la variable `PORT`; Railway la inyecta durante la ejecución.

La URL remota del MCP tendrá esta forma:

```text
https://tu-dominio.up.railway.app/mcp
```

## Variables

| Variable | Requerida | Descripción |
|---|---:|---|
| `DATABASE_URL` | Sí | Conexión PostgreSQL que contiene `dm_products`. |
| `HOST` | No | Interfaz de escucha. Por defecto `0.0.0.0`. |
| `PORT` | No | Puerto HTTP. Railway lo proporciona automáticamente. |
| `MCP_PATH` | No | Ruta del protocolo MCP. Por defecto `/mcp`. |
| `MCP_MAX_RESULTS` | No | Máximo de resultados permitidos. Por defecto `50`. |
| `MCP_DATABASE_CONNECT_TIMEOUT` | No | Timeout de PostgreSQL en segundos. Por defecto `10`. |

## Prueba rápida

Comprueba primero que el despliegue esté activo:

```bash
curl https://tu-dominio.up.railway.app/health
```

Para probar las herramientas con un cliente FastMCP:

```python
import asyncio
from fastmcp import Client


async def main() -> None:
    async with Client("https://tu-dominio.up.railway.app/mcp") as client:
        tools = await client.list_tools()
        print([tool.name for tool in tools])

        result = await client.call_tool("read_health_check", {})
        print(result)


asyncio.run(main())
```

## Seguridad de base de datos

Se recomienda usar un usuario PostgreSQL con permisos exclusivamente de lectura. Adicionalmente, cada conexión ejecuta `SET TRANSACTION READ ONLY` antes de consultar datos.
