from django.contrib import admin


class ModelAdminWithTools(admin.ModelAdmin):
    tools = []
    include_default_tools_after = True
    include_default_tools_before = False

    change_list_template = "utils/change_list_with_tools.html"


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'tools': self.tools,
            'include_default_tools_after': self.include_default_tools_after,
            'include_default_tools_before': self.include_default_tools_before
        })
        return super().changelist_view(request, extra_context)
