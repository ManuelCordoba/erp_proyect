# Seeders para Documents API

Este directorio contiene los archivos de seeders para poblar la base de datos con datos iniciales necesarios para probar la API de documentos.

## Uso del Management Command

Usa el management command de Django para crear los datos iniciales:

```bash
python manage.py seed_data
```

Para limpiar datos existentes antes de crear nuevos:

```bash
python manage.py seed_data --clear
```

### Datos que se crean:

1. **Company**: 
   - ID: `550e8400-e29b-41d4-a716-446655440000`
   - Nombre: "Empresa de Prueba S.A."
   - NIT: "900123456-7"

2. **Users** (todos con password: `test123`):
   - `sebastian` - Sebastian Garcia
   - `camilo` - Camilo Rodriguez
   - `juan` - Juan Perez
   - `admin` - Admin User (superuser)

El comando mostrará al finalizar:
- Los UUIDs de todos los usuarios creados
- Un ejemplo completo de request JSON listo para usar en la API

## Uso en la API

Una vez ejecutado el seeder, puedes usar estos datos en tus requests:

### Ejemplo de request para crear documento:

```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity": {
    "entity_type": "vehicle",
    "entity_id": "cualquier-uuid-aqui"
  },
  "document": {
    "name": "soat.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 123456,
    "bucket_key": "companies/550e8400-e29b-41d4-a716-446655440000/vehicles/uuid-veh/docs/soat-2025.pdf"
  },
  "validation_flow": {
    "enabled": true,
    "steps": [
      { "order": 1, "approver_user_id": "<uuid-de-sebastian>" },
      { "order": 2, "approver_user_id": "<uuid-de-camilo>" },
      { "order": 3, "approver_user_id": "<uuid-de-juan>" }
    ]
  }
}
```

**Nota**: Reemplaza los `<uuid-de-...>` con los UUIDs reales que muestra el comando `seed_data` al finalizar, o consulta:
- El admin de Django: `http://localhost:8000/admin/auth/user/`
- La base de datos directamente

## Archivos de ejemplo

- `example_request.json` - Ejemplo de request JSON completo
- `example_curl.sh` - Ejemplo de comando curl para probar la API
