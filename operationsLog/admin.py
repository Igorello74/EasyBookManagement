from django.contrib import admin
from django.template.loader import render_to_string

from operationsLog import backup
from operationsLog.models import LogRecord
from utils import cases


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
            super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)
            LogRecord.objects.log_create(obj, request.user)

    def delete_model(self, request, obj):
        LogRecord.objects.log_delete(obj, request.user)
        return super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if queryset.count() == 1:
            LogRecord.objects.log_delete(queryset[0], request.user)
        else:
            backup_file = backup.create_backup("bulk-delete")
            LogRecord.objects.log_bulk_delete(
                queryset, request.user,
                f"удаление {queryset.count()} {cases.gen_pl(queryset.model)}",
                backup_file)
        return super().delete_queryset(request, queryset)


def join_obj_reprs(ids: list, model, sep=", ", empty_value="-"):
    """Join str-representations of objects (with ids) of the given model.

    If these objects no more exist, join ids instead.
    """

    if ids:
        qs = model.objects.filter(pk__in=ids)
        if not qs:
            qs = ids
        return ", ".join(str(i) for i in qs)
    return empty_value


@admin.register(LogRecord)
class LogRecordAdmin(ModelAdminWithoutLogging):
    CONDITIONAL_FIELD_PREFIX = "~"
    readonly_fields_ = [
        "datetime",
        "~reason",
        "user",
        "content_type",
        "~obj_repr",
        "~deleted_obj",
        "~field_changes",
        "is_backup_created",
        "~objs_repr",
        "~modified_fields",
    ]

    date_hierarchy = "datetime"
    list_display = ["__html__", "datetime"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        fields = []
        for f in self.readonly_fields_:
            if f.startswith(self.CONDITIONAL_FIELD_PREFIX):
                f = f.removeprefix(self.CONDITIONAL_FIELD_PREFIX)
                if obj is not None and obj.details.get(f) is not None:
                    fields.append(f)
            else:
                fields.append(f)
        return fields

    @admin.display(description="Резервная копия")
    def is_backup_created(self, instance: LogRecord):
        if instance.backup_file:
            return "сохранена"
        return "не сохранена"

    @admin.display(description="Причина")
    def reason(self, instance: LogRecord):
        return instance.details["reason"]

    @admin.display(description="Объект")
    def obj_repr(self, instance: LogRecord):
        return instance.details["obj_repr"]

    @admin.display(description="Изменения")
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

    @admin.display(description="Объекты")
    def objs_repr(self, instance: LogRecord):
        title = "Объекты"
        if instance.operation == LogRecord.Operation.BULK_DELETE:
            title = "Удаленные объекты"
        elif instance.operation == LogRecord.Operation.BULK_UPDATE:
            title = "Изменённые объекты"

        expanded = True
        objs_num = len(instance.details["objs_repr"])
        if objs_num > 30:
            expanded = False

        return render_to_string(
            "operationsLog/objs_repr.html",
            {
                "objs": instance.details["objs_repr"].values(),
                "expanded": expanded,
                "title": title,
                "objs_num": objs_num,
            },
        )

    @admin.display(description="Изменённые поля")
    def modified_fields(self, instance: LogRecord):
        opts = instance.content_type.model_class()._meta
        results = []
        for field_name in instance.details["modified_fields"]:
            try:
                results.append(opts.get_field(field_name).verbose_name)
            except Exception:
                results.append(field_name)
        return ", ".join(results)

    @admin.display(description="Удалённый объект")
    def deleted_obj(self, instance: LogRecord):
        opts = instance.content_type.model_class()._meta
        obj = {}
        for field_name, value in instance.details["deleted_obj"].items():
            try:
                field = opts.get_field(field_name)
                verbose_name = field.verbose_name
                if field.many_to_many:
                    model = field.related_model
                    value = ", ".join(str(model.objects.get(pk=i)) for i in value)
                elif field.many_to_one:
                    model = field.related_model
                    value = str(model.objects.get(pk=value))
            except Exception:
                verbose_name = field_name
            obj[verbose_name] = value

        return render_to_string("operationsLog/deleted_obj.html", {"obj": obj})
