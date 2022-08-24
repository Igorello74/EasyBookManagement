from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from . import models
import readersRecords.models


@admin.register(models.Book)
class BookAdmin(admin.ModelAdmin):
    @admin.display(description="Количество экземпляров")
    @mark_safe
    def get_number_of_instances(self):
        individual = self.bookinstance_set.filter(represents_multiple=False).count()
        multiple = self.bookinstance_set.filter(represents_multiple=True).count()
        result = []
        
        if individual:
            result.append(f"{individual} индвидуальных")
        if multiple:
            result.append(f"{multiple} общих")

        if result:
            result = ', '.join(result)
        else:
            result = "0"

        return ('<a href="{href}?book_id={book_id}" '
                'title="Показать экземпляры"'
                'target="_blank" rel="noopener noreferrer">{result}</a>'
                ).format(
                    href=reverse(
                        "admin:booksRecords_bookinstance_changelist"),
                    book_id=self.id,
                    result=result
        )

    @admin.display(description="Количество взятых экземпляров")
    def get_num_of_taken_instances(self):
        return readersRecords.models.Reader.books.through.objects.filter(
            bookinstance__book=self).count()

    search_fields = ['name', 'authors', 'subject__name',
                     'grade', 'isbn',]

    list_display = (
        'name',
        'authors',
        'subject',
        'grade',
        get_number_of_instances,
        get_num_of_taken_instances
    )
    empty_value_display = ''

    list_filter = ('subject', 'grade')

    fieldsets = (
        ('Основная информация', {'fields': ('name', 'authors')}),

        ('Информация об издании',
         {'fields': ('publisher', 'city', 'year', 'edition')}),

        ("Идентификаторы",
         {'fields': ('isbn',)}),

        ("Учебная информация",
         {'fields': ('grade', 'subject')}),
    )

    autocomplete_fields = ['subject']


@admin.register(models.BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    @admin.display(description="взята")
    @mark_safe
    def get_taken_by(self, obj):
        taken_by_num = obj.taken_by.count()
        if taken_by_num > 1:
            return f"{taken_by_num} читателями"
        elif taken_by_num == 1:
            reader = obj.taken_by.all()[0]
            href = reverse(
                "admin:readersRecords_reader_change", args=(reader.id,)
            )
            return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{reader}</a>'
        else:
            return "нет"

    @admin.display(description="взята")
    @mark_safe
    def get_taken_by_verbose(self, obj):
        taken_by = list(obj.taken_by.all().only("id", "name", "group"))
        if taken_by:
            for ind, reader in enumerate(taken_by):
                href = reverse(
                    "admin:readersRecords_reader_change", args=(reader.id,)
                )
                taken_by[ind] = (
                    f'<a href="{href}" target="_blank" rel="noopener noreferrer",>{reader}</a>'
                )

            if len(taken_by) > 1:
                return ('; '.join(i for i in taken_by))

            else:
                return taken_by[0]
        else:
            return "нет"

    @admin.display(description="название")
    @mark_safe
    def get_book_name_with_link(self, obj):
        href = reverse("admin:booksRecords_book_change", args=(obj.book.id,))
        return (
            f'<a href="{href}" title="Редактировать книгу (не экземпляр)"'
            f'target="_blank" rel="noopener noreferrer">{obj.book.name}</a>')

    @admin.display(description="автор")
    def get_book_authors(self, obj):
        return obj.book.authors

    list_display = ('barcode', 'get_book_name_with_link',
                    "represents_multiple", 'status', 'get_taken_by')
    readonly_fields = ('get_taken_by_verbose',)
    list_filter = ("represents_multiple", 'status', 'book__grade')
    fields = ('status', 'barcode', 'book', "represents_multiple",
              "notes", 'get_taken_by_verbose')
    autocomplete_fields = ['book']
    search_fields = ('barcode', 'book__name', 'book__authors')


@admin.register(models.Subject)
class SubjectAdmin(admin.ModelAdmin):
    search_fields = ['name']
