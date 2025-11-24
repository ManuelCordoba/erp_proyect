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
            approver_usernames = [f'aprobador{i}' for i in range(1, 6)]
            Approver.objects.filter(user__username__in=approver_usernames).delete()
            # Don't delete all users, only test users
            User.objects.filter(username__in=approver_usernames).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create 2 Companies
        companies_data = [
            {
                'id': uuid.UUID('550e8400-e29b-41d4-a716-446655440000'),
                'name': 'Empresa de Prueba S.A.',
                'nit': '900123456-7',
                'active': True
            },
            {
                'id': uuid.UUID('660e8400-e29b-41d4-a716-446655440001'),
                'name': 'Empresa Tecnológica S.A.S.',
                'nit': '900987654-3',
                'active': True
            },
        ]

        companies_created = []
        for company_data in companies_data:
            company, created = Company.objects.get_or_create(
                id=company_data['id'],
                defaults={
                    'name': company_data['name'],
                    'nit': company_data['nit'],
                    'active': company_data['active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created company: {company.name} (ID: {company.id})'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Company already exists: {company.name} (ID: {company.id})'))
            companies_created.append(company)

        # Create 5 Generic Approver Users
        users_data = [
            {
                'username': 'aprobador1',
                'email': 'aprobador1@example.com',
                'first_name': 'Aprobador',
                'last_name': 'Uno',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'aprobador2',
                'email': 'aprobador2@example.com',
                'first_name': 'Aprobador',
                'last_name': 'Dos',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'aprobador3',
                'email': 'aprobador3@example.com',
                'first_name': 'Aprobador',
                'last_name': 'Tres',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'aprobador4',
                'email': 'aprobador4@example.com',
                'first_name': 'Aprobador',
                'last_name': 'Cuatro',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'username': 'aprobador5',
                'email': 'aprobador5@example.com',
                'first_name': 'Aprobador',
                'last_name': 'Cinco',
                'is_staff': False,
                'is_superuser': False,
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
            
            # Create Approver for each user
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
        
        self.stdout.write(f'\nCompanies ({len(companies_created)}):')
        for company in companies_created:
            self.stdout.write(f'  • {company.name}')
            self.stdout.write(f'    ID: {company.id}')
            self.stdout.write(f'    NIT: {company.nit}')
            self.stdout.write(f'    Active: {company.active}')
        
        self.stdout.write(f'\nUsers (Password for all: test123):')
        for user_data in users_data:
            user = User.objects.get(username=user_data['username'])
            self.stdout.write(f'  • {user.username}')
            self.stdout.write(f'    User ID: {user.id}')
            self.stdout.write(f'    Email: {user.email}')
            self.stdout.write(f'    Name: {user.first_name} {user.last_name}')
        
        self.stdout.write(f'\nApprovers ({len(approvers_created)}):')
        for approver in approvers_created:
            self.stdout.write(f'  • {approver.user.username}')
            self.stdout.write(f'    Approver UUID: {approver.id}')
            self.stdout.write(f'    User: {approver.user.get_full_name()}')
            self.stdout.write(f'    Active: {approver.active}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60 + '\n'))