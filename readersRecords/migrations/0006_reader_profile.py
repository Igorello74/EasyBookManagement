# Generated by Django 4.0.2 on 2022-06-17 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('readersRecords', '0005_alter_reader_books'),
    ]

    operations = [
        migrations.AddField(
            model_name='reader',
            name='profile',
            field=models.CharField(blank=True, help_text='например, ИТ, ТЕХ и т. п. (заглавными буквами)', max_length=20, verbose_name='профиль'),
        ),
    ]
