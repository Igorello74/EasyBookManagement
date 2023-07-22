from django.contrib import admin
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
            backup_file = backup.create_backup()
            LogRecord.objects.log_bulk_delete(
                queryset, request.user, backup_file=backup_file
            )
        return super().delete_queryset(request, queryset)
