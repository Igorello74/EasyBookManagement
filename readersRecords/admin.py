from datetime import datetime

from django.contrib import admin
from django.db import models
from django.http import FileResponse

from .models import Reader
from .widgets import ChoicesjsTextWidget


@admin.action(description='Экспортировать выбранных читателей')
def export_to_file(modeladmin, request, queryset):
    file_path = queryset.export_to_file(
        ".xlsx",
        {'id': 'id',
         'name': 'имя',
         'group': 'класс',
         'profile': 'профиль',
         'first_lang': 'язык 1',
         'second_lang': 'язык 2',
         'role': "роль",
         'books': "книги"
         },
        ['books'],
    )

    return FileResponse(
        open(file_path, "rb"),
        filename=datetime.now().strftime("Экспорт читателей %d-%m-%Y.xlsx"),
        as_attachment=True,
        headers={"Content-Type": "application/vnd.openxmlformats"
                 "-officedocument.spreadsheetml.sheet"})


@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    def get_books(self):
        return ' 🔷 '.join(str(i.book.name) for i in self.books.all())
    get_books.short_description = "книги"

    list_display = ("id", "name", "role", "group", get_books)
    search_fields = ("name", 'group', 'id')
    readonly_fields = ("id",)
    fieldsets = (
        ("Основная информация", {"fields": ('name', 'role', 'id', 'notes')}),
        ("Учебная информация", {
         "fields": ('group', 'profile', 'first_lang', 'second_lang')}),
        ("Книги", {"fields": ("books",), "classes": ("books",)})
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': ChoicesjsTextWidget}
    }

    list_filter = ("group",)

    actions = [export_to_file]

    class Media:
        js = ('js/reader.js',)
        css = {'all': ('css/reader.css',)}
