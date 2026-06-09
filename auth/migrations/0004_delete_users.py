from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clinic_auth', '0003_migrate_roles_to_groups'),
    ]

    operations = [
        migrations.DeleteModel(name='Users'),
    ]
