from django.contrib import admin

from .models import Reader

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    def get_books(self):
        return ', '.join(str(i) for i in self.books.all())
    get_books.short_description = "книги"

    list_display = ("name", "role", "group", get_books)
    search_fields = ("name", 'group')
    autocomplete_fields = ['books']
