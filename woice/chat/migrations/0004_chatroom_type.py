# Generated by Django 3.2.4 on 2021-07-06 00:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chatroom_unique_name_and_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatroom',
            name='type',
            field=models.CharField(choices=[('public', 'Public'), ('private', 'Private')], default='public', max_length=10),
        ),
    ]
