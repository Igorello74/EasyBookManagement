from django.contrib import admin

from .models import Reader

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ("role", "name", "group")
    search_fields = ("name", 'group')
