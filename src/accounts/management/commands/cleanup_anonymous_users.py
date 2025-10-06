"""
Management command to cleanup old anonymous users.

Usage:
    python manage.py cleanup_anonymous_users
    python manage.py cleanup_anonymous_users --dry-run
    python manage.py cleanup_anonymous_users --days 60
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete old anonymous users based on ANONYMOUS_USER_RETENTION_DAYS setting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Override retention days from settings',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        # Get retention days
        retention_days = options.get('days') or getattr(
            settings, 'ANONYMOUS_USER_RETENTION_DAYS', 30
        )
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Query old anonymous users
        old_anonymous_users = User.objects.filter(
            is_anonymous=True,
            date_joined__lt=cutoff_date
        )
        
        count = old_anonymous_users.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No old anonymous users to delete.')
            )
            return
        
        # Show what will be deleted
        self.stdout.write(
            self.style.WARNING(
                f'Found {count} anonymous user(s) older than {retention_days} days '
                f'(created before {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")})'
            )
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.NOTICE('DRY RUN - No users will be deleted.')
            )
            
            # Show sample users
            sample_users = old_anonymous_users[:5]
            self.stdout.write('\nSample users that would be deleted:')
            for user in sample_users:
                self.stdout.write(
                    f'  - ID: {user.id}, Device ID: {user.device_id}, '
                    f'Created: {user.date_joined.strftime("%Y-%m-%d %H:%M:%S")}'
                )
            
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more')
        else:
            # Delete users
            deleted_count, _ = old_anonymous_users.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} old anonymous user(s).'
                )
            )
            
            # Log statistics
            remaining = User.objects.filter(is_anonymous=True).count()
            self.stdout.write(
                f'Remaining anonymous users: {remaining}'
            )

