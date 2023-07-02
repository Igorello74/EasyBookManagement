import re
from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.defaulttags import register
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.text import Truncator
from django.views import View
from django.contrib import messages

from importExport.views import ExportView, ImportView
from utils import defaultdict_recursed

from .models import Reader


@method_decorator(
    permission_required("readersRecords.add_reader", raise_exception=True),
    name="dispatch",
)
class ReaderImportView(ImportView):
    model = Reader
    template_name = "readersRecords/import.html"
    headers_mapping = {
        "name": "имя",
        "group": "класс",
        "profile": "профиль",
        "first_lang": "язык 1",
        "second_lang": "язык 2",
        "role": "роль",
    }
    page_title = "Добавить читателей из файла"


@method_decorator(
    permission_required("readersRecords.view_reader", raise_exception=True),
    name="dispatch",
)
class ReaderExportView(ExportView):
    model = Reader
    headers_mapping = {
        "id": "id",
        "name": "Имя",
        "group": "Класс",
        "profile": "Профиль",
        "first_lang": "Язык 1",
        "second_lang": "Язык 2",
        "books": "Книги",
    }
    related_fields = {"books"}

    @staticmethod
    def format_related(qs) -> str:
        result = []
        for count, i in enumerate(qs.select_related("book"), 1):
            author = Truncator(i.book.authors).words(1)
            result.append(f"{count}. {i.book.name} ({author}) — [{i.barcode}]")

        return "\n".join(result)

    def get_filename(self):
        return f"База читателей {datetime.now():%d-%m-%Y}.xlsx"


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@method_decorator(
    permission_required("readersRecords.change_reader", raise_exception=True),
    name="dispatch",
)
class ChangeStudentsGroupView(View):
    TO_DELETE = "К УДАЛЕНИЮ"

    def post(self, request, queryset=None, *args, **kwargs):
        if queryset is not None:
            queryset = queryset.annotate(Count("books"))
            readers = queryset.filter(role=Reader.STUDENT).values(
                "id", "name", "group", "books__count"
            )
            readers_grouped = defaultdict_recursed()
            groups = set()
            for r in readers:
                group_num, group_letter = re.match(
                    r"(\d+)(.+)", r["group"]
                ).groups()
                group_num = int(group_num)
                groups.add((group_num, group_letter))
                readers_grouped[group_num][r["group"]][r["id"]] = r

            new_groups = {}
            for group_num, group_letter in groups:
                if group_num < settings.READERSRECORDS_MAX_GRADE:
                    new_groups[
                        f"{group_num}{group_letter}"
                    ] = f"{group_num+1}{group_letter}"
                else:
                    new_groups[f"{group_num}{group_letter}"] = self.TO_DELETE

            readers_grouped = dict(sorted(readers_grouped.items()))

            return TemplateResponse(
                request,
                "readersRecords/change-group.html",
                {
                    "readers_grouped": readers_grouped,
                    "title": "Перевод учеников в следующий класс",
                    "new_groups": new_groups,
                },
            )
        else:
            students_to_update = []
            students_to_delete_ids = []

            for key, val in request.POST.items():
                if key.startswith("student-"):
                    student_id = int(key.removeprefix("student-"))
                    if val != self.TO_DELETE:
                        students_to_update.append(
                            Reader(id=student_id, group=val)
                        )
                    else:
                        students_to_delete_ids.append(student_id)

            students_to_delete = Reader.objects.filter(
                id__in=students_to_delete_ids
            )

            students_to_delete_with_books = students_to_delete.annotate(
                Count("books")
            ).filter(books__count__gt=0)

            if students_to_delete_with_books.exists():
                return HttpResponse(
                    "Ты совершаешь ошибку. Нельзя удалять тех, на ком записаны книги!!!"
                )
            else:
                Reader.objects.bulk_update(students_to_update, ("group",))
            return redirect("admin:readersRecords_reader_changelist")


@method_decorator(
    permission_required("readersRecords.change_reader", raise_exception=True),
    name="dispatch",
)
class UpdateStudentsGradeView(View):
    def get(self, request, *args, **kwargs):
        students = Reader.objects.filter(role=Reader.STUDENT)
        graduating = students.filter(
            group__startswith=str(settings.READERSRECORDS_MAX_GRADE)
        )
        graduating_with_books = graduating.annotate(Count("books")).filter(
            books__count__gt=0
        )

        if graduating_with_books:
            s = ", ".join(
                f"{i.name}, {i.group} ({i.books__count} книг)"
                for i in graduating_with_books
            )
            messages.error(
                request,
                f"У следующих выпускающихся учеников не сданы книги: {s}",
            )
            return redirect("admin:readersRecords_reader_changelist")

        if request.GET.get("confirm") is None:
            return render(
                request,
                "readersRecords/update-grade-confirm.html",
                {
                    "title": "Вы уверены?",
                    "opts": Reader._meta,
                    "view_name": "Перевести учеников в следующий класс",
                    "has_view_permission": True,
                    "graduating": graduating,
                },
            )
        to_update = []
        for s in students.only("group"):
            match = re.match(r"(\d+)(.+)", s.group)

            if match is None:
                continue

            grade, letter = match.groups()
            grade = int(grade)
            if grade < settings.READERSRECORDS_MAX_GRADE:
                s.group = f"{grade+1}{letter}"
                to_update.append(s)

        deleted_count = graduating.delete()[0]
        updated_count = Reader.objects.bulk_update(to_update, ("group",))

        messages.success(
            request,
            f"{updated_count} учеников переведены в следующий класс. "
            f"{deleted_count} выпускников удалено.",
        )

        return redirect("admin:readersRecords_reader_changelist")


change_students_group = ChangeStudentsGroupView.as_view()
import_readers = admin.site.admin_view(ReaderImportView.as_view())
export_readers = admin.site.admin_view(ReaderExportView.as_view())
update_students_grade = admin.site.admin_view(UpdateStudentsGradeView.as_view())
