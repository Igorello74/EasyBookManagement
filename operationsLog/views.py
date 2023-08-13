from django.http import HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib import messages

from operationsLog.models import LogRecord, ReversionError
from utils.views import CustomAdminViewMixin

import traceback

Operation = LogRecord.Operation
REVERT_OPERATION_MESSAGES = {
    Operation.CREATE: "будет удалён созданный объект",
    Operation.UPDATE: "будут отменены изменения над объектом",
    Operation.DELETE: "будет восстановлен удалённый объект",
    Operation.BULK_CREATE: "будут удалены созданные объекты",
    Operation.BULK_UPDATE: "будут отменены изменения над объектами",
    Operation.BULK_DELETE: "будут восстановлены удалённые объекты",
    Operation.REVERT: "будет восстановлено отменённое действие",
}


class RevertLogRecordView(CustomAdminViewMixin, TemplateView):
    model = LogRecord
    template_name = "operationsLog/revert-logrecord-confirm.html"

    def get(self, request, id, *args, **kwargs):
        if "confirm" in request.GET:
            return self.confirm(id)
        else:
            return self.not_confirm(id)

    def confirm(self, id):
        try:
            logrecord = get_object_or_404(LogRecord, id=id)
            logrecord_repr = str(logrecord)
            logrecord.revert(self.request.user)
            messages.success(self.request, f"Успешно отменено действие {logrecord_repr}")
        except ReversionError as e:
            messages.error(self.request, "Невозможно отменить действие. Обратитесь к администратору.")
        return redirect("admin:operationsLog_logrecord_changelist")

    def not_confirm(self, id):
        logrecord = get_object_or_404(LogRecord, id=id)

        self.title = f"Отменить {logrecord}"

        context = self.get_context_data(
            logrecord=logrecord,
            revert_operation=REVERT_OPERATION_MESSAGES[logrecord.operation],
        )
        return self.render_to_response(context)


revert_logrecord = RevertLogRecordView.as_view()
