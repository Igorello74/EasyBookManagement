# Generated by Django 4.0.2 on 2022-07-12 16:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('booksRecords', '0009_alter_book_subject'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Желательно придерживаться какого-то единообразия. Например:\nвместо ̶ф̶р̶а̶н̶ц̶у̶з̶с̶к̶и̶й̶ ̶я̶з̶ы̶к̶ ̶в̶т̶о̶р̶о̶й — второй французский язык.\nИли: вместо ̶м̶а̶т̶е̶м̶а̶т̶и̶к̶а̶ ̶у̶г̶л̶у̶б̶л̶ё̶н̶н̶а̶я — углублённая математика', max_length=100, unique=True, verbose_name='название')),
            ],
        ),
        migrations.RemoveIndex(
            model_name='book',
            name='booksRecord_grade_81461b_idx',
        ),
        migrations.AddIndex(
            model_name='book',
            index=models.Index(fields=['grade', 'subject'], name='booksRecord_grade_8773af_idx'),
        ),
        migrations.AlterField(
            model_name='book',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='booksRecords.subject'),
        ),
    ]
