# Generated by Django 4.2.3 on 2023-08-22 10:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("booksRecords", "0018_rename_barcode_bookinstance_id"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="bookinstance",
            options={
                "verbose_name": "издание книги",
                "verbose_name_plural": "издания книг",
            },
        ),
        migrations.RemoveField(
            model_name="book",
            name="edition",
        ),
        migrations.RemoveField(
            model_name="book",
            name="isbn",
        ),
        migrations.RemoveField(
            model_name="book",
            name="year",
        ),
        migrations.RemoveField(
            model_name="bookinstance",
            name="represents_multiple",
        ),
        migrations.AddField(
            model_name="bookinstance",
            name="edition",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="номер издания"
            ),
        ),
        migrations.AddField(
            model_name="bookinstance",
            name="publication_year",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="год издания"
            ),
        ),
        migrations.AlterField(
            model_name="book",
            name="authors",
            field=models.TextField(
                blank=True,
                help_text="Авторы книги (сокращённо) через запятую",
                verbose_name="автор(-ы)",
            ),
        ),
        migrations.AlterField(
            model_name="subject",
            name="name",
            field=models.CharField(
                max_length=100, unique=True, verbose_name="название"
            ),
        ),
        migrations.AlterField(
            model_name="bookinstance",
            name="book",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                to="booksRecords.book",
                verbose_name="книга",
            ),
        ),
    ]
