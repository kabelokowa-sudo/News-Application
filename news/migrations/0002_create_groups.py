from django.contrib.auth.management import create_permissions
from django.db import migrations


def create_groups_and_permissions(apps, schema_editor):
    """
    Sets up the Reader, Editor and Journalist groups with the right
    permissions. Runs as part of migrate so it works on any database -
    dev, test, or MariaDB - without redoing shell commands each time.

    Django normally creates ContentTypes and Permissions automatically
    after all migrations finish (via a post_migrate signal), which is
    too late for this migration to rely on. The loop below is Django's
    own documented workaround: it forces create_permissions() to run
    early using the historical/frozen app registry passed into this
    migration, instead of the signal.
    """
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    article_ct = ContentType.objects.get(app_label='news', model='article')
    newsletter_ct = ContentType.objects.get(app_label='news', model='newsletter')

    def get_perm(content_type, codename_prefix):
        return Permission.objects.get(
            content_type=content_type,
            codename__startswith=codename_prefix
        )

    # Reader - view only
    reader_group, _ = Group.objects.get_or_create(name='Reader')
    reader_group.permissions.set([
        get_perm(article_ct, 'view'),
        get_perm(newsletter_ct, 'view'),
    ])

    # Editor - view, change, delete
    editor_group, _ = Group.objects.get_or_create(name='Editor')
    editor_group.permissions.set([
        get_perm(article_ct, 'view'),
        get_perm(article_ct, 'change'),
        get_perm(article_ct, 'delete'),
        get_perm(newsletter_ct, 'view'),
        get_perm(newsletter_ct, 'change'),
        get_perm(newsletter_ct, 'delete'),
    ])

    # Journalist - add, view, change, delete
    journalist_group, _ = Group.objects.get_or_create(name='Journalist')
    journalist_group.permissions.set([
        get_perm(article_ct, 'add'),
        get_perm(article_ct, 'view'),
        get_perm(article_ct, 'change'),
        get_perm(article_ct, 'delete'),
        get_perm(newsletter_ct, 'add'),
        get_perm(newsletter_ct, 'view'),
        get_perm(newsletter_ct, 'change'),
        get_perm(newsletter_ct, 'delete'),
    ])


def reverse_groups(apps, schema_editor):
    """Deletes the groups if this migration ever gets unapplied."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Reader', 'Editor', 'Journalist']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions, reverse_groups),
    ]