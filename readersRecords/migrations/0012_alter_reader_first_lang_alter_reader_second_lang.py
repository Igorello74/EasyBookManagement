# Generated by Django 4.0.8 on 2023-05-29 19:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readersRecords', '0011_remove_reader_readersreco_role_46b1c9_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='first_lang',
            field=models.CharField(blank=True, max_length=20, verbose_name='Первый язык'),
        ),
        migrations.AlterField(
            model_name='reader',
            name='second_lang',
            field=models.CharField(blank=True, max_length=20, verbose_name='Второй язык'),
        ),
    ]
