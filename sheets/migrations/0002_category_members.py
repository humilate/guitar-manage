from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sheets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='member_categories', to=settings.AUTH_USER_MODEL, verbose_name='成员'),
        ),
    ]
