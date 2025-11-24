# Colección de Postman - ERP Documents API

Esta colección de Postman contiene todos los endpoints del sistema de gestión de documentos ERP para facilitar las pruebas de la API.

## 📦 Archivos Incluidos

- `ERP_Documents_API.postman_collection.json` - Colección principal con todos los endpoints
- `ERP_Documents_API.postman_environment.json` - Variables de entorno para configuración

## 🚀 Cómo Importar

### Opción 1: Importar desde Postman

1. Abre Postman
2. Haz clic en **Import** (botón superior izquierdo)
3. Arrastra y suelta los archivos `.json` o haz clic en **Upload Files**
4. Selecciona ambos archivos:
   - `ERP_Documents_API.postman_collection.json`
   - `ERP_Documents_API.postman_environment.json`
5. Haz clic en **Import**

### Opción 2: Importar desde URL (si está en un repositorio)

1. En Postman, haz clic en **Import**
2. Selecciona la pestaña **Link**
3. Pega la URL del archivo JSON
4. Haz clic en **Continue** y luego en **Import**

## ⚙️ Configuración

### 1. Seleccionar el Entorno

Después de importar, asegúrate de seleccionar el entorno **"ERP Documents API - Local"** en el selector de entornos (esquina superior derecha de Postman).

### 2. Actualizar Variables

Las siguientes variables están preconfiguradas pero puedes actualizarlas según tus necesidades:

- **base_url**: URL base de la API (por defecto: `http://localhost:8000/api/documents`)
- **company_id**: UUID de la empresa (ejemplo incluido)
- **entity_id**: UUID de la entidad (vehículo, empleado, etc.)
- **approver_user_id_1, approver_user_id_2, ...**: UUIDs de los aprobadores

**Nota:** Las variables `document_id` y `bucket_key` se actualizan automáticamente cuando ejecutas las requests correspondientes.

## 📋 Endpoints Incluidos

### 1. Upload & Download URLs

- **Get Presigned Upload URL**: Genera URL pre-firmada para subir archivo a S3
- **Get Presigned Download URL**: Genera URL pre-firmada para descargar archivo de S3

### 2. Document Management

- **Create Document**: Crea un documento con flujo de validación
- **Create Document (Without Validation)**: Crea un documento sin flujo de validación

### 3. Document Validation

- **Approve Document**: Aprueba un paso de validación del documento
- **Reject Document**: Rechaza un paso de validación del documento

## 🔄 Flujo de Trabajo Recomendado

1. **Obtener URL de Upload**
   - Ejecuta "Get Presigned Upload URL"
   - Copia la `upload_url` y los `fields` de la respuesta

2. **Subir Archivo a S3** (fuera de Postman)
   - Usa la `upload_url` y `fields` para hacer un POST multipart/form-data
   - El `bucket_key` se guardará automáticamente en las variables

3. **Crear Documento**
   - Ejecuta "Create Document"
   - El `document_id` se guardará automáticamente en las variables

4. **Validar Documento**
   - Ejecuta "Approve Document" o "Reject Document"
   - Usa el `document_id` que se guardó automáticamente

## 🧪 Tests Automáticos

Cada request incluye tests automáticos que validan:
- Códigos de estado HTTP correctos
- Estructura de la respuesta
- Presencia de campos requeridos
- Actualización automática de variables

## 📝 Notas Importantes

1. **Autenticación**: Si tu API requiere autenticación, agrega los headers necesarios en cada request o configura la autenticación a nivel de colección.

2. **Variables Dinámicas**: 
   - `document_id` y `bucket_key` se actualizan automáticamente
   - Puedes usar `{{$randomUUID}}` en los requests para generar UUIDs aleatorios

3. **Tipos de Entidad Válidos**:
   - `vehicle`
   - `employee`
   - `other`

4. **Flujo de Validación**:
   - Los pasos de validación deben tener `order` secuencial (1, 2, 3, ...)
   - Cada `approver_user_id` debe ser un UUID válido de un Approver existente

## 🔧 Personalización

Puedes crear múltiples entornos para diferentes ambientes:
- **Local**: `http://localhost:8000/api/documents`
- **Development**: `https://dev-api.example.com/api/documents`
- **Production**: `https://api.example.com/api/documents`

Para crear un nuevo entorno, duplica el archivo de entorno y actualiza las variables según corresponda.

## 📚 Documentación Adicional

Para más detalles sobre cada endpoint, consulta el `README.md` principal del proyecto.

