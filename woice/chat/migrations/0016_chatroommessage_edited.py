# Generated by Django 3.2.4 on 2021-07-21 00:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0015_alter_chatroommember_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroommessage',
            name='edited',
            field=models.BooleanField(default=False),
        ),
    ]
