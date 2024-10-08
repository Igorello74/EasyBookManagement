# Generated by Django 4.0.2 on 2022-07-13 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0014_alter_bookinstance_status'),
        ('readersRecords', '0007_alter_reader_books'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='books',
            field=models.ManyToManyField(blank=True, db_table='bookTaking', related_name='taken_by', to='booksRecords.BookInstance', verbose_name='книги'),
        ),
    ]
