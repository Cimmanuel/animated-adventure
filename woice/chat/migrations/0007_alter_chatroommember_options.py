# Generated by Django 3.2.4 on 2021-07-06 10:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0006_alter_chatroom_creator'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chatroommember',
            options={'verbose_name': 'Chatroom member', 'verbose_name_plural': 'Chatroom members'},
        ),
    ]