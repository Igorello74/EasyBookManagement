# Generated by Django 3.2.6 on 2021-08-26 05:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('readersRecords', '0001_initial'),
        ('booksRecords', '0003_auto_20210826_0022'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookinstance',
            name='notes',
            field=models.TextField(blank=True, verbose_name='заметки'),
        ),
        migrations.AddField(
            model_name='bookinstance',
            name='taken_by',
            field=models.ForeignKey(blank=True, help_text='Читатель, взявший книгу', null=True, on_delete=django.db.models.deletion.PROTECT, to='readersRecords.reader', verbose_name='взята'),
        ),
        migrations.AddIndex(
            model_name='bookinstance',
            index=models.Index(fields=['taken_by'], name='booksRecord_taken_b_a3710a_idx'),
        ),
        migrations.AddIndex(
            model_name='bookinstance',
            index=models.Index(fields=['book'], name='booksRecord_book_id_b76bcf_idx'),
        ),
    ]
