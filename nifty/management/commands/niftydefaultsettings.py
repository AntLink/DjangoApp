from nifty.data import *
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Add Nifty default settings in the database."

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help='Fill in the user id that has been added.')

    def handle(self, *args, **kwargs):
        user_id = kwargs['id']
        if user_id == None:
            self.stdout.write(self.style.SUCCESS(f'Before running this command, make sure the admin user has been added. and run comment niftydefaultsettings --id 1 (if user_id==1)"'))
        else:
            load_admin_theme_setting_stores(user_id=user_id)
            load_site_setting_stores(user_id=user_id)
            load_admin_setting_stores(user_id=user_id)
            self.stdout.write(self.style.SUCCESS(f'Nifty successfully added standard settings to user id {user_id}!'))
