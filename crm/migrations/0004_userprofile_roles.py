# Generated by Django 3.0.3 on 2020-03-08 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_auto_20200308_1336'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='roles',
            field=models.ManyToManyField(blank=True, null=True, to='crm.Role'),
        ),
    ]