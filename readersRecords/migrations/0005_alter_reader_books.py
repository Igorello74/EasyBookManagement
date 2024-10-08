# Generated by Django 4.0.2 on 2022-06-16 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0008_book_notes_alter_book_city_alter_book_edition_and_more'),
        ('readersRecords', '0004_alter_reader_books'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='books',
            field=models.ManyToManyField(blank=True, db_table='bookTaking', limit_choices_to={'status': 0}, to='booksRecords.BookInstance', verbose_name='книги'),
        ),
    ]
