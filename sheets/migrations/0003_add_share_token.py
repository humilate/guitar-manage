from django.conf import settings
from django.db import migrations, models
import uuid
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sheets', '0002_category_members'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='is_shared',
            field=models.BooleanField(default=False, verbose_name='是否共享'),
        ),
        migrations.AddField(
            model_name='category',
            name='share_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='分享令牌'),
        ),
        migrations.CreateModel(
            name='SheetImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='sheet_images/')),
                ('page_number', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('sheet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='sheets.guitarsheet')),
            ],
        ),
        migrations.RemoveField(
            model_name='guitarsheet',
            name='image',
        ),
    ]
