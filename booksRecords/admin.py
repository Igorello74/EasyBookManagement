from django.contrib import admin
from django.utils.safestring import mark_safe

from . import models


@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin):
    def number_of_instances(self):
        return self.bookinstance_set.count()
    number_of_instances.short_description = "Количество экземпляров"

    search_fields = ['name', 'authors', 'subject',
                     'grade', 'isbn', 'inventory_number']

    list_display = (
        'authors',
        'name',
        'isbn',
        'inventory_number',
        number_of_instances,
    )

    fieldsets = (
        ("Идентификаторы", {'fields':
                            ('isbn', 'inventory_number')
                            }),

        ('Основная информация', {'fields':
                                 ('name', 'authors')
                                 }),

        ('Информация об издании', {'fields':
                                   ('publisher', 'city',
                                    'year', 'edition')
                                   }),

        ("Учебная информация", {'fields':
                                ('grade', 'subject')
                                }),
    )


@admin.register(models.BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    @admin.display(description="взята")
    def get_taken_by(self, obj):
        taken_by = obj.taken_by.all()
        if taken_by:
            if len(taken_by) > 1:
                return mark_safe(
                    f"<strong style='color: red; font-size: 2em'>!!!</strong> {'; '.join(str(i) for i in taken_by)}"
                )
            else:
                return taken_by[0]
        else:
            return "нет"

    list_display = ('barcode', 'book', 'status')
    readonly_fields = ('status', 'get_taken_by')
    fields = ('status', 'barcode', 'book', "notes", 'get_taken_by')
    autocomplete_fields = ['book']
    search_fields = ('barcode', 'book__name', 'book__authors')
