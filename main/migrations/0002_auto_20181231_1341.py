# Generated by Django 2.0.8 on 2018-12-31 21:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cert',
            name='cert_size',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
