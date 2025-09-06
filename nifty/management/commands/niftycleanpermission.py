from django.core.management import BaseCommand
from django.contrib.auth.models import Permission, ContentType


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        ContentType.objects.filter(model__icontains='contenttype').delete()
        ContentType.objects.filter(model__icontains='session').delete()
        # ContentType.objects.filter(model__icontains='logentry').delete()
        ContentType.objects.filter(model__icontains='mypermission').delete()
        ContentType.objects.filter(model__icontains='permission').delete()

        Permission.objects.filter(codename__icontains='_contenttype').delete()
        Permission.objects.filter(codename__icontains='_session').delete()
        Permission.objects.filter(codename__icontains='_permission').delete()
        Permission.objects.filter(codename__icontains='_profile').delete()
        # Permission.objects.filter(codename__icontains='view_').delete()
        # Permission.objects.filter(codename__icontains='view_').delete()
        Permission.objects.filter(codename__icontains='_media').delete()

        Permission.objects.filter(codename__icontains='_user').delete()
        Permission.objects.filter(codename__icontains='_group').delete()

        Permission.objects.filter(codename__icontains='_mypermission').delete()

        Permission.objects.filter(codename='add_site').delete()
        Permission.objects.filter(codename='delete_site').delete()

        Permission.objects.filter(codename='add_admin').delete()
        Permission.objects.filter(codename='delete_admin').delete()

        Permission.objects.filter(codename='add_logentry').delete()

        Permission.objects.filter(codename='add_setting').delete()
        Permission.objects.filter(codename='delete_setting').delete()
        Permission.objects.filter(codename='change_setting').delete()
        Permission.objects.filter(codename='view_setting').delete()

        ##################################################################################################################################

        #add user
        if Permission.objects.filter(codename='add_myuser').count() == 1:
            admin_st = Permission.objects.get(codename='add_myuser')
            admin_st.content_type = ContentType.objects.get(model='myuser')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='add_myuser').delete()
            Permission(content_type=ContentType.objects.get(model='myuser'), codename='add_myuser',name='Can add user').save()

        #change user
        if Permission.objects.filter(codename='change_myuser').count() == 1:
            admin_st = Permission.objects.get(codename='change_myuser')
            admin_st.content_type = ContentType.objects.get(model='myuser')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_myuser').delete()
            Permission(content_type=ContentType.objects.get(model='myuser'), codename='change_myuser',name='Can change user').save()

        #delete user
        if Permission.objects.filter(codename='delete_myuser').count() == 1:
            admin_st = Permission.objects.get(codename='delete_myuser')
            admin_st.content_type = ContentType.objects.get(model='myuser')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_myuser').delete()
            Permission(content_type=ContentType.objects.get(model='myuser'), codename='delete_myuser',name='Can delete user').save()

        #View user
        if Permission.objects.filter(codename='view_myuser').count() == 1:
            admin_st = Permission.objects.get(codename='view_myuser')
            admin_st.content_type = ContentType.objects.get(model='myuser')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_myuser').delete()
            Permission(content_type=ContentType.objects.get(model='myuser'), codename='view_myuser',name='Can view user').save()

        ##################################################################################################################################

        # add group
        if Permission.objects.filter(codename='add_mygroup').count() == 1:
            admin_st = Permission.objects.get(codename='add_mygroup')
            admin_st.content_type = ContentType.objects.get(model='mygroup')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='add_mygroup').delete()
            Permission(content_type=ContentType.objects.get(model='mygroup'), codename='add_mygroup', name='Can add group').save()

        # change group
        if Permission.objects.filter(codename='change_mygroup').count() == 1:
            admin_st = Permission.objects.get(codename='change_mygroup')
            admin_st.content_type = ContentType.objects.get(model='mygroup')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_mygroup').delete()
            Permission(content_type=ContentType.objects.get(model='mygroup'), codename='change_mygroup', name='Can change group').save()

        # delete group
        if Permission.objects.filter(codename='delete_mygroup').count() == 1:
            admin_st = Permission.objects.get(codename='delete_mygroup')
            admin_st.content_type = ContentType.objects.get(model='mygroup')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='delete_mygroup').delete()
            Permission(content_type=ContentType.objects.get(model='mygroup'), codename='delete_mygroup', name='Can delete group').save()

        # View group
        if Permission.objects.filter(codename='view_mygroup').count() == 1:
            admin_st = Permission.objects.get(codename='view_mygroup')
            admin_st.content_type = ContentType.objects.get(model='mygroup')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_mygroup').delete()
            Permission(content_type=ContentType.objects.get(model='mygroup'), codename='view_mygroup', name='Can view group').save()

        ##############################################################################################################################

        #admin setting change
        if Permission.objects.filter(codename='change_admin').count() == 1:
            admin_st = Permission.objects.get(codename='change_admin')
            admin_st.content_type = ContentType.objects.get(model='admin')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_admin').delete()
            Permission(content_type=ContentType.objects.get(model='admin'), codename='change_admin',name='Can change admin setting').save()

        # admin setting view
        if Permission.objects.filter(codename='view_admin').count() == 1:
            admin_st = Permission.objects.get(codename='view_admin')
            admin_st.content_type = ContentType.objects.get(model='admin')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_admin').delete()
            Permission(content_type=ContentType.objects.get(model='admin'), codename='view_admin', name='Can view admin setting').save()

        ##################################################################################################################################

        #site setting change
        if Permission.objects.filter(codename='change_site').count() == 1:
            admin_st = Permission.objects.get(codename='change_site')
            admin_st.content_type = ContentType.objects.get(model='site')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='change_site').delete()
            Permission(content_type=ContentType.objects.get(model='site'), codename='change_site',name='Can change site setting').save()

        #site setting view
        if Permission.objects.filter(codename='view_site').count() == 1:
            admin_st = Permission.objects.get(codename='view_site')
            admin_st.content_type = ContentType.objects.get(model='site')
            admin_st.save()
        else:
            Permission.objects.filter(codename__icontains='view_site').delete()
            Permission(content_type=ContentType.objects.get(model='site'), codename='view_site',name='Can view site setting').save()



        # Permission.objects.filter()
        print('Sukses.......................')
