# Generated by Django 3.2.6 on 2021-09-05 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0006_booktaking_is_returned'),
        ('readersRecords', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='reader',
            name='books',
            field=models.ManyToManyField(through='booksRecords.BookTaking', to='booksRecords.BookInstance'),
        ),
    ]