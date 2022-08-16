# Generated by Django 3.2.6 on 2021-08-24 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isbn', models.BigIntegerField(blank=True, db_index=True, help_text='Обязательно заполнять при наличии такового.\nЧтобы ускорить процесс, можно отсканировать штрихкод с ISBN-ом сканером (обычно располагается на обратной стороне книги)', null=True, verbose_name='ISBN номер')),
                ('name', models.CharField(max_length=65, verbose_name='название')),
                ('authors', models.TextField(help_text='Авторы книги (сокращённо) через запятую', verbose_name='автор(-ы)')),
                ('inventory_number', models.BigIntegerField(verbose_name='инвентарный номер')),
                ('year', models.SmallIntegerField(verbose_name='год издания')),
                ('publisher', models.CharField(max_length=20, verbose_name='издательство')),
                ('edition', models.SmallIntegerField(verbose_name='номер издания')),
                ('city', models.CharField(help_text='город издания книги, без "г. "', max_length=30, verbose_name='город издания')),
                ('grade', models.CharField(blank=True, help_text='Может быть диапазоном, к примеру: "7-9"', max_length=5, verbose_name='класс')),
                ('subject', models.CharField(blank=True, help_text='Например: "математика", "русский язык", "математика углублённая"', max_length=20, verbose_name='предмет')),
            ],
        ),
    ]
