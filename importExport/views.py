from datetime import datetime

from django.core.exceptions import ImproperlyConfigured
from django.db.models import QuerySet
from django.http import FileResponse
from django.views import View
from django.views.generic.edit import FormView

from importExport import BadFileError, InvalidDataError, base
from utils.views import CustomAdminViewMixin

from .forms import ImportForm


class ImportView(CustomAdminViewMixin, FormView):
    """Create or update model instancies from an xlsx or csv file

    You have to set some attributes when subclassing this view:

    model: the model subclass;

    template_name: name of the template to use when rendering this view
        (you can extend "importExport/import.html");

    headers_mapping (dict): a mapping of model fields
        to column headers (custom column names);

    virtual_fields: a mapping of virtual field names to VirtualField instances.

    ignore_errors: whether row-level errors should be silenced,

    title: html title to be set on the import page

    For more information on some properties,
    check importExport.base.import_from_file.

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
    virtual_fields = None
    ignore_errors = False
    title = None

    def form_valid(self, form):
        if not (self.model and self.headers_mapping):
            raise ImproperlyConfigured(
                'You must set the "model" and "headers_mapping" attributes in the '
                "subclass definition"
            )

        try:
            result = base.import_from_file(
                self.model,
                self.request.FILES["file"],
                self.headers_mapping,
                self.ignore_errors,
                self.virtual_fields,
                self.request.user,
            )
            context = self.get_context_data(**result)

        except BadFileError:
            context = self.get_context_data(bad_format=True)
        except InvalidDataError as e:
            context = self.get_context_data(invalid=e.invalid_objs)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        if not self.title:
            self.title = f"Импортировать {self.model._meta.verbose_name.title()}"
        context = super().get_context_data(**kwargs)
        return context


class ExportView(View):
    model = None
    headers_mapping = None
    related_fields: set[str] = set()
    file_format = ".xlsx"

    @staticmethod
    def format_related(qs: QuerySet) -> str:
        raise NotImplementedError(
            "format_related method has to be implemented in the subclass"
        )

    def get_filename(self):
        model_name = self.model._meta.verbose_name.title()
        return f"Экспорт {model_name} {datetime.now():%d-%m-%Y}{self.file_format}"

    def get(self, request, queryset=None):
        if queryset is None:
            queryset = self.model.objects.all()

        file_path = base.export_queryset_to_file(
            queryset,
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
