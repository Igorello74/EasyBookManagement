
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .bulk_operations import ColumnNotFoundError, import_readers, BadFile
from .forms import ImportForm


def render_import_xlsx(request, err_obj: Exception = None,
                       created: int = 0, updated: int = 0):
    context = {'form': ImportForm}

    if err_obj:
        if isinstance(err_obj, ColumnNotFoundError):
            context['missing_columns'] = err_obj.missing_columns
        elif isinstance(err_obj, BadFile):
            context['bad_format'] = True
        
    context['created'] = created
    context['updated'] = updated

    return render(request, "readersRecords/import-form.html", context)


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_xlsx(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = import_readers(request.FILES['file'], {
                    'name': 'имя',
                    'group': 'класс',
                    'profile': 'профиль',
                    'first_lang': 'язык 1',
                    'second_lang': 'язык 2',
                    'role': "роль"
                })
            except (ColumnNotFoundError, BadFile) as e:
                return render_import_xlsx(request, err_obj=e)
            else:
                return render_import_xlsx(request, **result)

    elif request.method == "GET":
        return render_import_xlsx(request)
