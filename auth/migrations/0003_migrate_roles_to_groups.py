from django.db import migrations, models

ROLE_NAMES = ['admin', 'doctor', 'patient', 'receptionist']


def migrate_roles_to_groups(apps, schema_editor):
    Users = apps.get_model('clinic_auth', 'Users')
    Group = apps.get_model('auth', 'Group')
    db_alias = schema_editor.connection.alias

    # Ensure all four role groups exist.
    groups = {}
    for name in ROLE_NAMES:
        group, _ = Group.objects.using(db_alias).get_or_create(name=name)
        groups[name] = group

    # Assign each user's current role as a group membership.
    for profile in Users.objects.using(db_alias).select_related('user').filter(user__isnull=False):
        role = profile.role
        if role in groups:
            profile.user.groups.add(groups[role])


def reverse_groups_to_roles(apps, schema_editor):
    """Best-effort reverse: read the user's first matching role group back into profile.role."""
    Users = apps.get_model('clinic_auth', 'Users')
    db_alias = schema_editor.connection.alias

    for profile in Users.objects.using(db_alias).select_related('user').filter(user__isnull=False):
        role_group = (
            profile.user.groups.filter(name__in=ROLE_NAMES).first()
        )
        if role_group:
            profile.role = role_group.name
            profile.save(using=db_alias, update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('clinic_auth', '0002_users_email_users_password_hash_users_username'),
    ]

    operations = [
        # Step 1: migrate existing role data to groups before removing the field.
        migrations.RunPython(migrate_roles_to_groups, reverse_code=reverse_groups_to_roles),

        # Step 2: remove the fields that are now redundant.
        migrations.RemoveField(model_name='users', name='role'),
        migrations.RemoveField(model_name='users', name='email'),
        migrations.RemoveField(model_name='users', name='password'),
        migrations.RemoveField(model_name='users', name='username'),
    ]
