# Generated by Django 3.2.6 on 2021-08-25 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Reader',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('TE', 'учитель'), ('ST', 'ученик'), ('OTH', 'иной')], max_length=3, verbose_name='роль')),
                ('name', models.CharField(max_length=100, verbose_name='полное имя')),
                ('notes', models.TextField(blank=True, max_length=500, verbose_name='заметки')),
                ('group', models.CharField(blank=True, help_text='номер и строчная литера класса без пробела', max_length=3, verbose_name='класс')),
                ('first_lang', models.CharField(blank=True, choices=[('en', 'Английский'), ('de', 'Немецкий'), ('fr', 'Французкий'), ('zh', 'Китайский'), ('it', 'Итальянский')], max_length=2, verbose_name='Первый язык')),
                ('second_lang', models.CharField(blank=True, choices=[('en', 'Английский'), ('de', 'Немецкий'), ('fr', 'Французкий'), ('zh', 'Китайский'), ('it', 'Итальянский')], max_length=2, verbose_name='Второй язык')),
            ],
            options={
                'verbose_name': 'читатель',
                'verbose_name_plural': 'читатели',
                'ordering': ['role', 'group', 'name'],
            },
        ),
        migrations.AddIndex(
            model_name='reader',
            index=models.Index(fields=['name'], name='readersReco_name_79ae88_idx'),
        ),
        migrations.AddIndex(
            model_name='reader',
            index=models.Index(fields=['role', 'name'], name='readersReco_role_46b1c9_idx'),
        ),
        migrations.AddIndex(
            model_name='reader',
            index=models.Index(fields=['group', 'name'], name='readersReco_group_bc8b32_idx'),
        ),
    ]
