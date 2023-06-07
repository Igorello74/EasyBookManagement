
from datetime import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
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
