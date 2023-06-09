
import re
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.defaulttags import register
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.text import Truncator
from django.views import View

from importExport.views import ExportView, ImportView

from .models import Reader


@method_decorator(staff_member_required, name="dispatch")
class ReaderImportView(ImportView):
    model = Reader
    template_name = "readersRecords/import.html"
    headers_mapping = {
        'name': 'имя',
        'group': 'класс',
        'profile': 'профиль',
        'first_lang': 'язык 1',
        'second_lang': 'язык 2',
        'role': "роль"
    }
    required_fields = ['name']
    page_title = "Загрузить базу читателей"


import_xlsx = ReaderImportView.as_view()


class ReaderExportView(ExportView):
    model = Reader
    headers_mapping = {
        'id': 'id',
        'name': 'Имя',
        'group': 'Класс',
        'profile': 'Профиль',
        'first_lang': 'Язык 1',
        'second_lang': 'Язык 2',
        'books': "Книги"
    }
    related_fields = {'books'}

    @staticmethod
    def format_related(qs) -> str:
        result = []
        for count, i in enumerate(qs.select_related("book"), 1):
            author = Truncator(i.book.authors).words(1)
            result.append(
                f"{count}. {i.book.name} ({author}) — [{i.barcode}]"
            )

        return "\n".join(result)

    def get_filename(self):
        return f"База читателей {datetime.now():%d-%m-%Y}.xlsx"


export_xlsx = ReaderExportView.as_view()


class defaultdict_recursed(defaultdict):
    def __init__(self):
        super().__init__(defaultdict_recursed)

    def __getitem__(self, key):
        if key in {"items", 'keys', 'values'}:
            raise KeyError
        return super().__getitem__(key)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


class ReadersUpdateGradeAction(View):
    def post(self, request, queryset=None, *args, **kwargs):
        if queryset is not None:
            queryset = queryset.annotate(Count("books"))
            readers = queryset.filter(role=Reader.STUDENT).values(
                "id", "name", "group", "books__count")
            readers_grouped = defaultdict_recursed()
            groups = set()
            for r in readers:
                group_num, group_letter = re.match(
                    "(\d+)(.+)", r['group']).groups()
                group_num = int(group_num)
                groups.add((group_num, group_letter))
                readers_grouped[group_num][r['group']][r['id']] = r

            new_groups = {}
            for group_num, group_letter in groups:
                if group_num < settings.READERSRECORDS_MAX_GRADE:
                    new_groups[f"{group_num}{group_letter}"] = f"{group_num+1}{group_letter}"
                else:
                    new_groups[f"{group_num}{group_letter}"] = "К УДАЛЕНИЮ"
            
            readers_grouped = dict(sorted(readers_grouped.items()))

            return TemplateResponse(
                request,
                "readersRecords/update-grade.html",
                {
                    "readers_grouped": readers_grouped,
                    "title": "Перевод учеников в следующий класс",
                    'new_groups': new_groups
                }
            )
        else:
            students = []
            for key, val in request.POST.items():
                if key.startswith('student-'):
                    students.append(Reader(id=key.removeprefix("student-"), group=val))
            Reader.objects.bulk_update(students, ("group",))
            return redirect("admin:readersRecords_reader_changelist")

    def get(self, request, *args, **kwargs):
        return HttpResponse("ok get.")


update_grade = ReadersUpdateGradeAction.as_view()
