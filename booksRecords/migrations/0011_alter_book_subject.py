# Generated by Django 4.0.2 on 2022-07-12 17:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0010_subject_remove_book_booksrecord_grade_81461b_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='subject',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='booksRecords.subject'),
        ),
    ]
