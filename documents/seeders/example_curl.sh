#!/bin/bash
# Example curl command to create a document
# Replace the UUIDs with the actual user IDs from the seeder output

COMPANY_ID="550e8400-e29b-41d4-a716-446655440000"
SEBASTIAN_UUID="REEMPLAZAR_CON_UUID_DE_SEBASTIAN"
CAMILO_UUID="REEMPLAZAR_CON_UUID_DE_CAMILO"
JUAN_UUID="REEMPLAZAR_CON_UUID_DE_JUAN"

curl -X POST http://localhost:8000/api/documents/ \
  -H "Content-Type: application/json" \
  -d "{
    \"company_id\": \"$COMPANY_ID\",
    \"entity\": {
      \"entity_type\": \"vehicle\",
      \"entity_id\": \"123e4567-e89b-12d3-a456-426614174000\"
    },
    \"document\": {
      \"name\": \"soat.pdf\",
      \"mime_type\": \"application/pdf\",
      \"size_bytes\": 123456,
      \"bucket_key\": \"companies/$COMPANY_ID/vehicles/123e4567-e89b-12d3-a456-426614174000/docs/soat-2025.pdf\"
    },
    \"validation_flow\": {
      \"enabled\": true,
      \"steps\": [
        { \"order\": 1, \"approver_user_id\": \"$SEBASTIAN_UUID\" },
        { \"order\": 2, \"approver_user_id\": \"$CAMILO_UUID\" },
        { \"order\": 3, \"approver_user_id\": \"$JUAN_UUID\" }
      ]
    }
  }"

