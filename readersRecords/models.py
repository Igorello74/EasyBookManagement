from django.db import models


LANGUAGES = (
    ('en', 'Английский'),
    ('de', 'Немецкий'),
    ('fr', 'Французкий'),
    ('zh', 'Китайский'),
    ('it', 'Итальянский'),
)

class Reader(models.Model):
    '''
    Модель описывает читателя.
    '''
    
    TEACHER = "TE"
    STUDENT = "ST"
    OTHER = "OTH"
    ROLE_CHOICES = [
        (TEACHER, "учитель"), (STUDENT, "ученик"), (OTHER, "иной")
    ]

    role = models.CharField(
        choices=ROLE_CHOICES,
        max_length=3,
        verbose_name="роль"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="полное имя"        
    )    
    notes = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="заметки"
    )
    
    # Student specific info
    group = models.CharField(
        max_length=3,
        verbose_name="класс",
        help_text="номер и строчная литера класса без пробела",
        blank=True,
    )
    
    first_lang = models.CharField(
        max_length=2,
        choices=LANGUAGES,
        verbose_name='Первый язык',
        blank=True,
    )
    
    second_lang = models.CharField(
        max_length=2,
        choices=LANGUAGES,
        verbose_name='Второй язык',
        blank=True,
    )
    
    class Meta:
        indexes = (
            models.Index(fields=['name']),
            models.Index(fields=['role', 'name']),
            models.Index(fields=['group', 'name']),

        )
        ordering = ['role', 'group', 'name']
        
        verbose_name = "читатель"
        verbose_name_plural = 'читатели'