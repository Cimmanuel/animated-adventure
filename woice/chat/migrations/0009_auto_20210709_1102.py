# Generated by Django 3.2.4 on 2021-07-09 10:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0008_invitelink'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitelink',
            name='chatroom',
            field=models.ForeignKey(limit_choices_to={'type': 'private'}, on_delete=django.db.models.deletion.CASCADE, related_name='invite_link', to='chat.chatroom'),
        ),
        migrations.AlterField(
            model_name='invitelink',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
