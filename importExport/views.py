from django.contrib.admin import site as admin_site
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.edit import FormView

from importExport import BadFileError, ColumnNotFoundError

from .forms import ImportForm


class ImportView(FormView):
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

    template_name = None
    form_class = ImportForm
    model = None
    headers_mapping = None
    required_fields = []
    page_title = None

    def form_valid(self, form):
        try:
            assert all([self.model, self.headers_mapping])
            # check if the subclass is properly configured

            result = self.model.objects.import_from_file(
                self.request.FILES['file'],
                self.headers_mapping,
                self.required_fields
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
        except ColumnNotFoundError as e:
            context = self.get_context_data(missing_columns=e.missing_columns)
        except BadFileError:
            context = self.get_context_data(bad_format=True)
        else:
            context = self.get_context_data(**result)

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        if not self.page_title:
            self.page_title = f"Импортировать {self.model._meta.verbose_name.title()}"
        
        kwargs.update({
            'form': ImportForm,
            'title': self.page_title,
            'is_nav_sidebar_enabled': True,
            'available_apps': admin_site.get_app_list(self.request)
        })
        return super().get_context_data(**kwargs)
