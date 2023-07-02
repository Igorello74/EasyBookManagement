from django.contrib import admin
from django.db import models
from django.db.models import Count
from django.urls import reverse_lazy

from utils.admin import ModelAdminWithTools

from .models import Reader
from .views import export_readers, change_students_group
from .widgets import ChoicesjsTextWidget


@admin.action(description="Экспортировать выбранных читателей")
def export_action(modeladmin, request, queryset):
    return export_readers(request, queryset)


@admin.action(description="Перевести учеников в другой класс")
def change_group_action(modeladmin, request, queryset):
    return change_students_group(request, queryset)


@admin.register(Reader)
class ReaderAdmin(ModelAdminWithTools):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(Count("books"))

        return qs

    @admin.display(description="Количество взятых книг")
    def get_books_num(self):
        return self.books__count

    list_display = ("name", "role", "group", get_books_num)
    search_fields = ("name", "group", "id")
    readonly_fields = ("id",)
    fieldsets = (
        ("Основная информация", {"fields": ("name", "role", "id", "notes")}),
        ("Книги", {"fields": ("books",), "classes": ("books",)}),
        (
            "Учебная информация",
            {"fields": ("group", "profile", "first_lang", "second_lang")},
        ),
    )
    formfield_overrides = {
        models.ManyToManyField: {"widget": ChoicesjsTextWidget}
    }

    list_filter = ("role", "group")

    actions = [export_action, change_group_action]

    tools = [
        {
            "title": "Перевести учеников в следующий класс",
            "url": reverse_lazy("readers-update-grade"),
        },
        {
            "title": "Скачать читателей",
            "id": "exportlink",
            "url": reverse_lazy("readers-export"),
        },
        {
            "title": "Добавить читателей из файла",
            "id": "importlink",
            "url": reverse_lazy("readers-import"),
            "add_permission_required": True,
        },
    ]

    class Media:
        js = ("js/reader.js",)
        css = {"all": ("css/reader.css",)}
