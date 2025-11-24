"""
Management command to seed initial data for the documents API.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from documents.models import Company, Approver
import uuid


class Command(BaseCommand):
    help = 'Seeds initial data for the documents API (Company and Users)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Company.objects.all().delete()
            # Delete approvers first (they reference users)
            Approver.objects.filter(user__username__in=['sebastian', 'camilo', 'juan', 'admin']).delete()
            # Don't delete all users, only test users
            User.objects.filter(username__in=['sebastian', 'camilo', 'juan', 'admin']).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create Company
        company_id = uuid.UUID('550e8400-e29b-41d4-a716-446655440000')
        company, created = Company.objects.get_or_create(
            id=company_id,
            defaults={
                'name': 'Empresa de Prueba S.A.',
                'nit': '900123456-7',
                'active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created company: {company.name} (ID: {company.id})'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Company already exists: {company.name} (ID: {company.id})'))

        # Create Users
        users_data = [
            {
                'username': 'sebastian',
                'email': 'sebastian@example.com',
                'first_name': 'Sebastian',
                'last_name': 'Garcia',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'camilo',
                'email': 'camilo@example.com',
                'first_name': 'Camilo',
                'last_name': 'Rodriguez',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'juan',
                'email': 'juan@example.com',
                'first_name': 'Juan',
                'last_name': 'Perez',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            },
        ]

        approvers_created = []
        for user_data in users_data:
            user, user_created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    **user_data,
                    'is_active': True,
                }
            )
            if user_created:
                # Set a default password for all users
                user.set_password('test123')
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Created user: {user.username} (ID: {user.id}) - Password: test123'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'⚠ User already exists: {user.username} (ID: {user.id})'
                ))
            
            # Create Approver for each user (except admin, unless needed)
            if user_data['username'] != 'admin':  # Only create approvers for non-admin users
                approver, approver_created = Approver.objects.get_or_create(
                    user=user,
                    defaults={'active': True}
                )
                if approver_created:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created approver: {approver.user.username} (Approver ID: {approver.id})'
                    ))
                    approvers_created.append(approver)
                else:
                    self.stdout.write(self.style.WARNING(
                        f'⚠ Approver already exists for user: {user.username} (Approver ID: {approver.id})'
                    ))
                    approvers_created.append(approver)

        self.stdout.write(self.style.SUCCESS('\n✓ Data seeding completed!'))
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\nCompany:')
        self.stdout.write(f'  ID: {company.id}')
        self.stdout.write(f'  Name: {company.name}')
        self.stdout.write(f'  NIT: {company.nit}')
        
        self.stdout.write(f'\nUsers (Password for all: test123):')
        for user_data in users_data:
            user = User.objects.get(username=user_data['username'])
            self.stdout.write(f'  • {user.username}')
            self.stdout.write(f'    User ID: {user.id}')
            self.stdout.write(f'    Email: {user.email}')
            self.stdout.write(f'    Name: {user.first_name} {user.last_name}')
        
        self.stdout.write(f'\nApprovers (Use these UUIDs in API requests):')
        for approver in approvers_created:
            self.stdout.write(f'  • {approver.user.username}')
            self.stdout.write(f'    Approver UUID: {approver.id}')
            self.stdout.write(f'    User: {approver.user.get_full_name()}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Example API Request:'))
        self.stdout.write(self.style.SUCCESS('='*60))
        sebastian_approver = Approver.objects.get(user__username='sebastian')
        camilo_approver = Approver.objects.get(user__username='camilo')
        juan_approver = Approver.objects.get(user__username='juan')
        
        example_json = f'''{{
  "company_id": "{company.id}",
  "entity": {{
    "entity_type": "vehicle",
    "entity_id": "cualquier-uuid-aqui"
  }},
  "document": {{
    "name": "soat.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 123456,
    "bucket_key": "companies/{company.id}/vehicles/uuid-veh/docs/soat-2025.pdf"
  }},
  "validation_flow": {{
    "enabled": true,
    "steps": [
      {{ "order": 1, "approver_user_id": "{sebastian_approver.id}" }},
      {{ "order": 2, "approver_user_id": "{camilo_approver.id}" }},
      {{ "order": 3, "approver_user_id": "{juan_approver.id}" }}
    ]
  }}
}}'''
        self.stdout.write(example_json)
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

