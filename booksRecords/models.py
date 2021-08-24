from django.db import models

# Create your models here.

class Book(models.Model):
    """
    Формуляр книги. К нему могут относится множество экземпляров.
    """

    # Main fields
    isbn = models.BigIntegerField(
        verbose_name="ISBN номер", db_index=True, null=True, blank=True,
        help_text="Обязательно заполнять при наличии такового.\n"
        "Чтобы ускорить процесс, можно отсканировать штрихкод с ISBN-ом "
        "сканером (обычно располагается на обратной стороне книги)"
    )
    name = models.CharField(verbose_name="название", max_length=65,)
    authors = models.TextField(
        verbose_name="автор(-ы)", 
        help_text="Авторы книги (сокращённо) через запятую", 
    )
    inventory_number = models.BigIntegerField(
        verbose_name="инвентарный номер"
    )
    
    # Publication info
    year = models.SmallIntegerField(verbose_name="год издания")
    publisher = models.CharField(
        verbose_name="издательство", max_length=20)
    edition = models.SmallIntegerField(verbose_name='номер издания')
    city = models.CharField(
        max_length=30, verbose_name="город издания",
        help_text='город издания книги, без "г. "'
    )

    # Educational info
    grade = models.CharField(
        max_length=5, verbose_name="класс", blank=True,
        help_text="Может быть диапазоном, к примеру: \"7-9\""
    )
    subject = models.CharField(
        verbose_name="предмет", max_length=20, blank=True,
        help_text='Например: "математика", "русский язык", '
        '"математика углублённая"'
    )
