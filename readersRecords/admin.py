from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import Reader
from .views import export_xlsx, update_grade
from .widgets import ChoicesjsTextWidget


@admin.action(description='Экспортировать выбранных читателей')
def export_to_file(modeladmin, request, queryset):
    return export_xlsx(request, queryset)

@admin.action(description="Обновить класс учеников")
def update_grade_action(modeladmin, request, queryset):
    return update_grade(request, queryset)

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(Count("books"))

        return qs

    @admin.display(description="Количество взятых книг")
    def get_books_num(self):
        return self.books__count

    list_display = ("name", "role", "group", get_books_num)
    search_fields = ("name", 'group', 'id')
    readonly_fields = ("id",)
    fieldsets = (
        ("Основная информация", {"fields": ('name', 'role', 'id', 'notes')}),
        ("Книги", {"fields": ("books",), "classes": ("books",)}),
        ("Учебная информация", {
         "fields": ('group', 'profile', 'first_lang', 'second_lang')}),
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': ChoicesjsTextWidget}
    }

    list_filter = ("role", "group",)

    actions = [export_to_file, update_grade_action]

    class Media:
        js = ('js/reader.js',)
        css = {'all': ('css/reader.css',)}

admin.site.unregister(User)
admin.site.unregister(Group)