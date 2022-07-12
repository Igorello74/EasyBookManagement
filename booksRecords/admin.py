from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from . import models


@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin):
    @admin.display(description="Количество экземпляров")
    def number_of_instances(self):
        return self.bookinstance_set.count()

    search_fields = ['name', 'authors', 'subject__name',
                     'grade', 'isbn', 'inventory_number']

    list_display = (
        'id',
        'name',
        'authors',
        'subject',
        'grade',
        'inventory_number',
        number_of_instances,
    )
    empty_value_display = ''

    list_filter = ('subject', 'grade')

    fieldsets = (
        ('Основная информация', {'fields': ('name', 'authors')}),

        ('Информация об издании',
         {'fields': ('publisher', 'city', 'year', 'edition')}),

        ("Идентификаторы",
         {'fields': ('isbn', 'inventory_number')}),

        ("Учебная информация",
         {'fields': ('grade', 'subject')}),
    )

    autocomplete_fields = ['subject']


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

    @admin.display(description="название")
    @mark_safe
    def get_book_name_with_link(self, obj):
        href = reverse("admin:booksRecords_book_change", args=(obj.book.id,))
        return (f'<a href="{href}" title="Редактировать книгу (не экземпляр)"'
                f'target="_blank" rel="noopener noreferrer">{obj.book.name}</a>')

    @admin.display(description="автор")
    def get_book_authors(self, obj):
        return obj.book.authors

    list_display = ('barcode', 'get_book_name_with_link',
                    'get_book_authors', 'status')
    readonly_fields = ('status', 'get_taken_by')
    fields = ('status', 'barcode', 'book', "notes", 'get_taken_by')
    autocomplete_fields = ['book']
    search_fields = ('barcode', 'book__name', 'book__authors')


@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['name']
