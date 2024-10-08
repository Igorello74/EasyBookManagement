# Generated by Django 4.0.2 on 2022-06-20 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0008_book_notes_alter_book_city_alter_book_edition_and_more'),
        ('readersRecords', '0006_reader_profile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reader',
            name='books',
            field=models.ManyToManyField(blank=True, db_table='bookTaking', limit_choices_to={'status': 0}, related_name='taken_by', to='booksRecords.BookInstance', verbose_name='книги'),
        ),
    ]
