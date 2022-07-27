from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import  render
from django.views.decorators.http import require_http_methods

from .bulk_operations import import_from_xlsx, ColumnNotFoundError
from .forms import ImportForm


def render_import_xlsx(request, err_obj: ColumnNotFoundError = None, num_imported: int = 0):
    context = {'form': ImportForm}

    if err_obj:
        context['missing_columns'] = err_obj.missing_columns
    elif num_imported:
        context['num_imported'] = num_imported

    return render(request, "import-xlsx-form.html", context)


@staff_member_required
@require_http_methods(["GET", "POST"])
def import_xlsx(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                num_imported = import_from_xlsx(request.FILES['file'], {
                    'name': 'имя',
                    'group': 'класс',
                    'profile': 'профиль',
                    'first_lang': 'язык 1',
                    'second_lang': 'язык 2',
                })
            except ColumnNotFoundError as e:
                return render_import_xlsx(request, err_obj=e)

            else:
                return render_import_xlsx(request, num_imported=num_imported)

    elif request.method == "GET":
        return render_import_xlsx(request)
