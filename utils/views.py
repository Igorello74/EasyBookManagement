from django.views.generic.base import ContextMixin
from django.core.exceptions import ImproperlyConfigured


class CustomAdminViewMixin(ContextMixin):
    """You can use this mixin to create your custom admin views.
    This class provides some basic things like breadcrumbs, etc.
    - so that your view looks natural in the admin site.
    You need to mix in this class with a View class from django like this:

    class MyAdminView(CustomAdminViewMixin, TemplateView):
        def post(self, request):
            ...
            context = self.get_context(data=data)
            return self.render_to_response(context)
    `


    Properties you should set (at inheriting):
    - template_name - name of your template to use while rendering
    - model - the model your view deals with (it's required for breadcrumbs)
    - view_name - name of the current view (used in breadcrumbs as well)
    - title - title of the html page (defaults to view_name)
    - has_view_permision - whether this user has the view permission
      for this model (defaults to True). Most likely he has, so you
      don't need to set this attribute explicitly.
    
    You should inherit the utils/custom_admin_view.html template
    (use the "content" block to show the content, obviously)

    """

    template_name = "utils/custom_admin_view.html"
    model = None
    view_name = "Custom view"
    title = None
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
                "title": self.title or self.view_name,
            }
        )

        return context
