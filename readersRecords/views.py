
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.bulk_operations import ColumnNotFoundError, BadFile
from .forms import ImportForm
from .models import Reader


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
                result = Reader.objects.import_from_file(request.FILES['file'], ["name"])
            except (ColumnNotFoundError, BadFile) as e:
                return render_import_xlsx(request, err_obj=e)
            else:
                return render_import_xlsx(request, **result)

    elif request.method == "GET":
        return render_import_xlsx(request)
