from datetime import datetime

from django.contrib.admin import site as admin_site
from django.core.exceptions import ImproperlyConfigured
from django.http import FileResponse
from django.views import View
from django.views.generic.edit import FormView

from importExport import BadFileError
from utils.views import CustomAdminViewMixin

from .forms import ImportForm


class ImportView(CustomAdminViewMixin, FormView):
    """Create or update model instancies from an xlsx or csv file

    You have to set some attributes when subclassing this view:

    model: the model object with default manager (objects) set to
        an instance of the BulkManager;

    template_name: name of the template to use when rendering this view
        (you can extend "importExport/import.html");

    headers_mapping (dict): a mapping of model fields
        to column headers (custom column names);

    required_fields (list): a list of fields required to be filled;

    page_title: html title to be set on the import page

    The behaviour of importing is:
    if id is not provided in a row, a new instance is CREATED,
    if id is present, this entry is UPDATED.

    If any of required_fields is absent, the user is shown an error message.
    If file is of wrong format, an error is shown as well.


    Note: headers (in the file) are case insensitive.
    """

    template_name = "importExport/import.html"
    form_class = ImportForm
    model = None
    headers_mapping = None
    page_title = None

    def form_valid(self, form):
        try:
            assert self.model and self.headers_mapping
            # check if the subclass is properly configured

            result = self.model.objects.import_from_file(
                self.request.FILES["file"],
                self.headers_mapping,
            )

        except AssertionError:
            raise ImproperlyConfigured(
                "You must set model and"
                " headers_mapping in the subclass definition"
            )
        except AttributeError:
            raise ImproperlyConfigured(
                "You can only use ImportView with models whose default "
                "manager (objects) is an instance of BulkManager"
            )
        except BadFileError:
            context = self.get_context_data(bad_format=True)
        else:
            context = self.get_context_data(**result)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        if not self.title:
            self.title = (
                f"Импортировать {self.model._meta.verbose_name.title()}"
            )
        context = super().get_context_data(**kwargs)

        return context


class ExportView(View):
    model = None
    headers_mapping = None
    related_fields = set()
    file_format = ".xlsx"

    @staticmethod
    def format_related(qs) -> str:
        raise NotImplementedError(
            "format_related method has to be implemented in the subclass"
        )

    def get_filename(self):
        model_name = self.model._meta.verbose_name.title()
        return (
            f"Экспорт {model_name} {datetime.now():%d-%m-%Y}{self.file_format}"
        )

    def get(self, request, queryset=None):
        if queryset is None:
            queryset = self.model.objects.all()
        file_path = queryset.export_to_file(
            self.file_format,
            self.headers_mapping,
            self.related_fields,
            self.format_related,
        )

        return FileResponse(
            open(file_path, "rb"),
            filename=self.get_filename(),
            as_attachment=True,
        )

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)
