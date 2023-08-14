from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.utils.html import format_html

from operationsLog import models
from utils.views import CustomAdminViewMixin


Operation = models.LogRecord.Operation
REVERT_OPERATION_MESSAGES = {
    Operation.CREATE: "созданный объект будет удалён",
    Operation.UPDATE: "изменения над объектом будут отменены",
    Operation.DELETE: "удалённый объект будет восстановлен",
    Operation.BULK_CREATE: "созданные объекты будут удалены",
    Operation.BULK_UPDATE: "изменения над объектами будут отменены",
    Operation.BULK_DELETE: "удалённые объекты будут восстановлены",
    Operation.REVERT: "отменённое действие будет восстановлено",
}


class RevertLogRecordView(CustomAdminViewMixin, TemplateView):
    model = models.LogRecord
    template_name = "operationsLog/revert-logrecord-confirm.html"

    def get(self, request, id, *args, **kwargs):
        if "confirm" in request.GET:
            return self.confirm(id)
        else:
            return self.not_confirm(id)

    def confirm(self, id):
        try:
            logrecord = get_object_or_404(models.LogRecord, id=id)
            message = format_html(
                "Успешно отменено действие <span style="
                '"border: solid 1px #0000001f;padding: 2px;border-radius: 7px;">'
                "{}</span>",
                str(logrecord),
            )
            logrecord.revert(self.request.user)

            messages.success(self.request, message)
        except models.BackupCorruptedError:
            messages.error(
                self.request,
                "Невозможно отменить действие, "
                "потому что резервная копия повреждена. "
                "Обратитесь к администратору.",
            )
        except models.AlreadyRevertedErorr as e:
            try:
                dt = models.LogRecord.objects.get(id=e.reverted_by_id).datetime
                dt = dt.astimezone()  # convert the dt (in utc) to the local tz
                when = f" ({dt:%d.%m.%Y в %H:%M})"
            except Exception:
                when = ""

            messages.error(
                self.request,
                f"Это действие уже отменено{when}. Невозможно отменить его повторно.",
            )
        except models.ObjectDoesNotExistError:
            messages.error(
                self.request,
                "Невозможно изменить объект, который удалён. "
                "Сначала восстановите объект (отмените удаление объекта).",
            )
        except models.ReversionError as e:
            messages.error(
                self.request,
                "Невозможно отменить действие. Обратитесь к администратору.",
            )
        return redirect("admin:operationsLog_logrecord_changelist")

    def not_confirm(self, id):
        logrecord = get_object_or_404(models.LogRecord, id=id)

        self.title = f"Отменить {logrecord}"

        context = self.get_context_data(
            logrecord=logrecord,
            revert_operation=REVERT_OPERATION_MESSAGES[logrecord.operation],
        )
        return self.render_to_response(context)


revert_logrecord = RevertLogRecordView.as_view()
