# Generated by Django 4.0.2 on 2022-08-25 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchaseRecords', '0004_alter_bookpurchase_book'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookpurchase',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=6, verbose_name='цена экземпляра, ₽'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='custom_number',
            field=models.PositiveSmallIntegerField(help_text='номер в книге суммарного учёта', verbose_name='учётный номер (КСУ)'),
        ),
    ]
