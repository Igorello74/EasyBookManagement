# Generated by Django 3.2.6 on 2021-09-09 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0006_booktaking_is_returned'),
        ('readersRecords', '0003_alter_reader_books')
    ]

    operations = [
        migrations.DeleteModel(
            name='BookTaking',
        ),
    ]
