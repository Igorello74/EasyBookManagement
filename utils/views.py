from django.views.generic.base import ContextMixin
from django.core.exceptions import ImproperlyConfigured


class CustomAdminViewMixin(ContextMixin):
    """You can inherit this view to create your custom admin views.
    This class provides some basic things like breadcrumbs, etc.
    """

    template_name = "utils/custom_admin_view.html"
    model = None
    view_name = "Custom view"
    has_view_permission = True

    def get_context_data(self, **kwargs):
        if self.model is None:
            raise ImproperlyConfigured(
                'You have to set the "model" attribute to use that view'
            )

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "opts": self.model._meta,
                "view_name": self.view_name,
                "has_view_permission": self.has_view_permission,
            }
        )

        return context
