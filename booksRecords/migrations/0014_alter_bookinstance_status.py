# Generated by Django 4.0.2 on 2022-07-13 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0013_alter_book_subject'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookinstance',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'на учёте'), (1, 'снята с учёта')], default=0, verbose_name='статус'),
        ),
    ]
