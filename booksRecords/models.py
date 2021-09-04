from django.db import models

import readersRecords.models


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

    def __str__(self):
        return f"{self.authors}: {self.name}"

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=['authors']),
            models.Index(fields=['isbn']),
            models.Index(fields=['inventory_number']),
            models.Index(fields=["grade", "subject"])
        ]
        ordering = ['name']
        verbose_name = 'книга'
        verbose_name_plural = 'книги'


class BookInstance(models.Model):
    '''
    Описывает каждую книгу в библиотеке,
    каждый экземпляр.
    '''
    barcode = models.CharField(
        primary_key=True,
        unique=True,
        max_length=8,
        verbose_name="Штрихкод",
        help_text="идентификатор книги, уникальный для каждого "
        "экземпляра; совпадает с номером штрихкода на наклейке"
    )

    IN_STORAGE = 0
    ON_HANDS = 1
    EXPIRED = 2
    WRITTEN_OFF = 3
    
    STATUSES = (
        (IN_STORAGE, "в хранилище"),
        (ON_HANDS, "на руках"),
        (EXPIRED, "истёк срок возврата"),
        (WRITTEN_OFF, "снята с учёта")
    )
    status = models.PositiveSmallIntegerField(
        choices=STATUSES,
        editable=False,
        default=IN_STORAGE,
        verbose_name="статус"
    )
    
    notes = models.TextField(
        verbose_name="заметки",
        blank=True
    )
    
    
    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        verbose_name="книга",
        help_text="ссылка на модель Книга :Model:`booksRecord.Book`"
    )


    def __str__(self):
        return str(self.book)
    
    class Meta:
        ordering = ["barcode"]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['book']),

        ]
        verbose_name = "экземпляр книги"
        verbose_name_plural = "экземпляры книг"


class BookTaking(models.Model):
    reader = models.ForeignKey(
        readersRecords.models.Reader, on_delete=models.CASCADE,
        verbose_name="читатель"
    )
    book_instance = models.ForeignKey(
        "BookInstance", on_delete=models.CASCADE,
        limit_choices_to={'status': BookInstance.IN_STORAGE},
    )
    when_taken = models.DateTimeField(
        verbose_name="Дата и время взятия книги", auto_now_add=True
    )

    def save(self, *args, **kwargs):
        if not self.is_returned:
            self.book_instance.status = BookInstance.ON_HANDS
        else:
            self.book_instance.status = BookInstance.IN_STORAGE
        
        self.book_instance.save()
        super().save(*args, **kwargs)
