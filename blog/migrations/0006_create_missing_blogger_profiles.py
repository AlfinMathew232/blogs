from django.db import migrations
from django.utils import timezone

def create_blogger_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Blogger = apps.get_model('blog', 'Blogger')
    
    for user in User.objects.all():
        Blogger.objects.get_or_create(
            user=user,
            defaults={
                'bio': '',
                'created_date': timezone.now()
            }
        )

def reverse_blogger_profiles(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0005_blogger_created_date_blogger_profile_picture_and_more'),
    ]

    operations = [
        migrations.RunPython(create_blogger_profiles, reverse_blogger_profiles),
    ] 