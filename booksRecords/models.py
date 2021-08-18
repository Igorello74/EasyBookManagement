from django.db import models

# Create your models here.

class BookRecord(models.Model):
    """
    Формуляр книги. К нему могут относится множество экземпляров.
    """
    id = models.BigAutoField(
      unique=True, primary_key=True, verbose_name="идентификационный номер",
      help_text="Предпочтительно, чтобы этот номер соответствовал ISBN-коду книги (если он есть)"
    )
    name = models.CharField(verbose_name="название")
    authors = models.CharField(
      verbose_name="автор(-ы)", 
      help_text="Авторы книги (сокращённо) через запятую", 
      max_length=200
    )
    year = models.SmallIntegerField(verbose_name="год издания")
    publisher = models.CharField(verbose_name="издательство")
    # TODO
