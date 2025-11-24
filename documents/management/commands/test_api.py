"""
Management command to test the documents API endpoints.
Usage: python manage.py test_api
"""
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests
import json
import os
import mimetypes


class Command(BaseCommand):
    help = 'Test the documents API endpoints (upload, download, create document)'
    
    # Configuration - Modify these values as needed
    API_BASE_URL = "http://localhost:8000/api/documents"
    FILE_PATH = "tesla.jpg"  # Path to the file to upload
    CREATE_DB_DOCUMENT = True  # Whether to create document record after upload
    DOWNLOAD_FILE = True  # Whether to download file after upload


    # Document creation parameters
    COMPANY_ID = "550e8400-e29b-41d4-a716-446655440000"  # Company UUID
    ENTITY_TYPE = "vehicle"  # Entity type: vehicle, employee, other
    ENTITY_ID = "123e4567-e89b-12d3-a456-426614174000"  # Entity UUID
    BUCKET_KEY = ""  # Bucket key to upload the file to

    def handle(self, *args, **options):
        file_path = self.FILE_PATH
        api_base_url = self.API_BASE_URL
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise CommandError(f'File not found: {file_path}')
        
        # Get file info
        file_name = os.path.basename(file_path)
        self.BUCKET_KEY = f"companies/{self.COMPANY_ID}/documents/{self.ENTITY_TYPE}/{self.ENTITY_ID}/{file_name}"
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        file_size = os.path.getsize(file_path)
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('TEST: Documents API'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'\nFile: {file_path}')
        self.stdout.write(f'Name: {file_name}')
        self.stdout.write(f'Size: {file_size} bytes')
        self.stdout.write(f'Content-Type: {content_type}\n')
        
        # Step 1: Get presigned upload URL
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('STEP 1: Get presigned upload URL'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        upload_request = {
            "file_name": file_name,
            "content_type": content_type,
            "bucket_key": self.BUCKET_KEY
        }
        
        try:
            response = requests.post(
                f"{api_base_url}/presigned-upload-url/",
                json=upload_request,
                timeout=30
            )
            
            self.stdout.write(f'Status Code: {response.status_code}')
            
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f'❌ Error: {response.text}'))
                return
            
            presigned_data = response.json()
            self.stdout.write(f'Response: {json.dumps(presigned_data, indent=2)}')
            self.stdout.write(self.style.SUCCESS('\n✅ Presigned URL obtained'))
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Error connecting to API: {e}'))
            return
        
        # Step 2: Upload file to S3
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('STEP 2: Upload file to S3'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            files = {
                'file': (file_name, file_data, content_type)
            }
            
            upload_response = requests.post(
                presigned_data['upload_url'],
                data=presigned_data['fields'],
                files=files,
                timeout=300  # 5 minutes for large files
            )
            
            self.stdout.write(f'Status Code: {upload_response.status_code}')
            self.stdout.write(f'Response: {upload_response.text}')
            
            if upload_response.status_code == 204:
                self.stdout.write(self.style.SUCCESS('\n✅ File uploaded successfully to S3'))
                bucket_key = presigned_data['bucket_key']
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Error uploading file: {upload_response.text}'))
                return
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File not found: {file_path}'))
            return
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f'❌ Error uploading to S3: {e}'))
            return
        
        # Step 3: Create document record (optional)
        if self.CREATE_DB_DOCUMENT:
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('STEP 3: Create document record'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            company_id = self.COMPANY_ID
            entity_id = self.ENTITY_ID
            entity_type = self.ENTITY_TYPE
            
            if not company_id:
                self.stdout.write(self.style.ERROR('❌ COMPANY_ID is required in the code'))
                return
            
            if not entity_id:
                self.stdout.write(self.style.ERROR('❌ ENTITY_ID is required in the code'))
                return
            
            import uuid
            try:
                # Validate UUIDs
                uuid.UUID(company_id)
                uuid.UUID(entity_id)
            except ValueError:
                self.stdout.write(self.style.ERROR('❌ Invalid UUID format for COMPANY_ID or ENTITY_ID'))
                return
            
            document_request = {
                "company_id": company_id,
                "entity": {
                    "entity_type": entity_type,
                    "entity_id": entity_id
                },
                "document": {
                    "name": file_name,
                    "mime_type": content_type,
                    "size_bytes": file_size,
                    "bucket_key": bucket_key
                },
                "validation_flow": {
                    "enabled": True,
                    "steps": [
                    { "order": 1, "approver_user_id": "bdff8021-3f69-4f69-97b3-0376627aaf4e" },
                    { "order": 2, "approver_user_id": "7e33c89b-ad5d-40f5-bfc3-1f10bd652c1e" },
                    { "order": 3, "approver_user_id": "7c30d6b3-67fe-4ba6-933c-9e3c2b59ccee" }
                    ]
                }
            }
            
            try:
                doc_response = requests.post(
                    f"{api_base_url}/",
                    json=document_request,
                    timeout=30
                )
                
                self.stdout.write(f'Status Code: {doc_response.status_code}')
                
                if doc_response.status_code == 201:
                    doc_data = doc_response.json()
                    self.stdout.write(f'Response: {json.dumps(doc_data, indent=2)}')
                    self.stdout.write(self.style.SUCCESS('\n✅ Document created successfully'))
                    document_id = doc_data.get('id')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Error: {doc_response.text}'))
                    document_id = None
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'❌ Error creating document: {e}'))
                document_id = None
        else:
            document_id = None
        
        # Step 4: Download file (optional)
        if self.DOWNLOAD_FILE:
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('STEP 4: Download file from S3'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            
            try:
                # Use new GET endpoint if document_id is available, otherwise use POST endpoint
                if document_id:
                    self.stdout.write(f'Using GET endpoint with document_id: {document_id}')
                    download_url_response = requests.get(
                        f"{api_base_url}/{document_id}/download/",
                        timeout=30
                    )
                else:
                    self.stdout.write(f'Using POST endpoint with bucket_key: {bucket_key}')
                    download_request = {
                        "bucket_key": bucket_key
                    }
                    download_url_response = requests.post(
                        f"{api_base_url}/presigned-download-url/",
                        json=download_request,
                        timeout=30
                    )
                
                if download_url_response.status_code != 200:
                    self.stdout.write(self.style.ERROR(f'❌ Error getting download URL: {download_url_response.text}'))
                    return
                
                download_data = download_url_response.json()
                download_url = download_data['download_url']
                
                self.stdout.write(f'Download URL obtained: {download_url[:80]}...')
                
                # Download file
                file_download = requests.get(download_url, timeout=300)
                
                self.stdout.write(f'Status Code: {file_download.status_code}')
                self.stdout.write(f'Content Length: {len(file_download.content)} bytes')
                
                if file_download.status_code == 200:
                    # Save downloaded file
                    downloaded_filename = f"downloaded_{file_name}"
                    with open(downloaded_filename, "wb") as f:
                        f.write(file_download.content)
                    
                    self.stdout.write(self.style.SUCCESS(f'\n✅ File downloaded successfully'))
                    self.stdout.write(f'Saved as: {downloaded_filename}')
                else:
                    self.stdout.write(self.style.ERROR(f'\n❌ Error downloading: {file_download.text}'))
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'❌ Error downloading file: {e}'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'✅ File uploaded to S3')
        self.stdout.write(f'   Bucket Key: {bucket_key}')
        if document_id:
            self.stdout.write(f'✅ Document created in database')
            self.stdout.write(f'   Document ID: {document_id}')
        if self.DOWNLOAD_FILE:
            self.stdout.write(f'✅ File downloaded from S3')
        self.stdout.write(self.style.SUCCESS('=' * 60 + '\n'))
        
        # Show configuration used
        self.stdout.write(self.style.SUCCESS('\nConfiguration used:'))
        self.stdout.write(f'  API URL: {api_base_url}')
        self.stdout.write(f'  File: {file_path}')
        self.stdout.write(f'  Create Document: {self.CREATE_DB_DOCUMENT}')
        self.stdout.write(f'  Download File: {self.DOWNLOAD_FILE}')
        if self.CREATE_DB_DOCUMENT:
            self.stdout.write(f'  Company ID: {self.COMPANY_ID}')
            self.stdout.write(f'  Entity Type: {self.ENTITY_TYPE}')
            self.stdout.write(f'  Entity ID: {self.ENTITY_ID}')

