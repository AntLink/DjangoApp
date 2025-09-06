from django.core.management import BaseCommand
from django.urls.resolvers import RegexPattern, ResolverMatch
from django.urls import get_resolver
from django.contrib.auth.models import Permission


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        pass