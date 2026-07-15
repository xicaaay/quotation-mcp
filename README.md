# Quotation MCP Read

Servidor MCP en Python para consultar el catálogo `dm_products` de PostgreSQL. Esta versión es estrictamente de solo lectura.

## Herramientas expuestas

- `read_health_check`: valida conexión y conteo de productos.
- `read_database_catalog`: describe la entidad y campos disponibles.
- `read_search_products`: interpreta búsquedas libres o vagas.
- `read_refine_product_search`: profundiza una consulta anterior.
- `read_list_products`: aplica filtros exactos.
- `read_product_detail`: busca por UUID, código o nombre exacto.
- `read_compare_products`: compara varios productos.

## Instalación

```bash
uv sync
```

Si se parte de la versión inicial del proyecto, también puede instalarse con:

```bash
uv add "psycopg[binary]" pydantic pydantic-settings rapidfuzz
```

## Configuración

```bash
cp .env.example .env
```

Configura `DATABASE_URL` con la misma base PostgreSQL utilizada por el backend.

Se recomienda crear un usuario PostgreSQL con permisos exclusivamente de lectura. Además, cada conexión del MCP ejecuta `SET TRANSACTION READ ONLY`.

## Ejecución

```bash
uv run quotation-mcp
```

## Pruebas

```bash
uv add --dev pytest
uv run pytest
```

## Ejemplos de solicitudes

- "Busca algo para redes sociales".
- "Necesito una web por menos de 700 dólares".
- "Muéstrame servicios mensuales".
- "De la búsqueda anterior, solo opciones de desarrollo".
- "Compara DEV_LANDING_PAGE con DEV_INFO_WEBSITE".
