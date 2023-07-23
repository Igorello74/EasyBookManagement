from django.contrib import admin
from django.template.loader import render_to_string

from operationsLog import backup
from operationsLog.models import LogRecord


class ModelAdminWithoutLogging(admin.ModelAdmin):
    """
    ModelAdmin without default logging (admin.LogEntry).
    You don't really need this thing: it's uninformative and cumbersome.
    """

    log_addition = log_change = log_deletion = lambda *args, **kwargs: None


class LoggedModelAdmin(ModelAdminWithoutLogging):
    """
    ModelAdmin with advanced operations logging.
    Features:
    store changed fields and their values (before and after);
    store bulk operations wholly unlike the default LogEntry that stores
    each item separately, and therefore makes the delete action
    (with many items) extremely slow.
    """

    def save_model(self, request, obj, form, change):
        if change:
            LogRecord.objects.log_update(obj, form, request.user)
        else:
            LogRecord.objects.log_create(obj, request.user)
        return super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        LogRecord.objects.log_delete(obj, request.user)
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.count() == 1:
            LogRecord.objects.log_delete(queryset[0], request.user)
        else:
            backup_file = backup.create_backup("bulk-delete")
            LogRecord.objects.log_bulk_delete(
                queryset, request.user, backup_file=backup_file
            )
        return super().delete_queryset(request, queryset)


def join_obj_reprs(ids: list, model, sep=", ", empty_value="-"):
    """Join str-representations of objects with ids of the given model.

    If these objects no more exist, join ids instead.
    """

    if ids:
        qs = model.objects.filter(pk__in=ids)
        if not qs:
            qs = ids
        return ", ".join(str(i) for i in qs)
    return "-"


@admin.register(LogRecord)
class LogRecordAdmin(ModelAdminWithoutLogging):
    readonly_fields = [
        "datetime",
        "operation",
        "user",
        "content_type",
        "backup_file",
        "field_changes",
    ]

    @admin.display(description="Измененные поля")
    def field_changes(self, instance: LogRecord):
        if not instance.details.get("field_changes"):
            return "-"

        opts = instance.content_type.model_class()._meta
        fields = []

        for field_name, values in instance.details["field_changes"].items():
            old = values[0]
            new = values[1]
            try:
                field = opts.get_field(field_name)
                verbose_name = field.verbose_name

                if field.many_to_many:
                    old = join_obj_reprs(old, field.related_model)
                    new = join_obj_reprs(new, field.related_model)
            except Exception:
                verbose_name = field_name
            fields.append({"name": verbose_name, "old": old, "new": new})

        return render_to_string("operationsLog/field_changes.html", {"fields": fields})
