from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views.generic import TemplateView

from operationsLog import models, revert
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


@method_decorator(
    permission_required("operationsLog.view_logrecord", raise_exception=True),
    name="dispatch",
)
class RevertLogRecordView(CustomAdminViewMixin, TemplateView):
    model = models.LogRecord
    template_name = "operationsLog/revert-logrecord-confirm.html"

    def get(self, request, id, *args, **kwargs):
        if "confirm" in request.GET:
            return self.confirm(id)
        else:
            return self.not_confirm(id)

    def confirm(self, id):
        logrecord = get_object_or_404(models.LogRecord, id=id)
        logrecord_repr = str(logrecord)

        try:
            logrecord.revert(self.request.user)

        except revert.ManyToManyFieldError as e:
            messages.error(
                self.request,
                f'Невозможно отменить действие, так как поле "{e.field_verbose_name}"'
                f' содержит объект, несуществующий в базе данных (id={e.value})')
        except revert.IntegrityError:
            messages.error(
                self.request,
                'Невозможно отменить действие, так как какое-то поле '
                ' содержит объект, несуществующий в базе данных')
        except revert.BackupCorruptedError:
            messages.error(
                self.request,
                "Невозможно отменить действие, "
                "потому что резервная копия повреждена. "
                "Обратитесь к администратору.",
            )
        except revert.AlreadyRevertedError as e:
            try:
                dt = models.LogRecord.objects.get(id=e.reverted_by_id).datetime
                dt = dt.astimezone()  # convert the dt (in utc) to the local tz
                when = f" {dt:%d.%m.%Y в %H:%M}"
            except Exception:
                when = ""

            messages.error(
                self.request,
                f"Это действие уже отменено{when}. Невозможно отменить его повторно.",
            )
        except revert.ObjectDoesNotExistError:
            messages.error(
                self.request,
                "Невозможно изменить объект, который удалён. "
                "Сначала восстановите объект (отмените удаление объекта).",
            )
        except revert.ObjectAlreadyDeleted:
            messages.error(
                self.request,
                "Невозможно удалить объект, который уже удалён."
            )
        except revert.ReversionError:
            messages.error(
                self.request,
                "Невозможно отменить действие. Обратитесь к администратору.",
            )
        else:
            message = format_html(
                "Успешно отменено действие <span style="
                '"border: solid 1px #0000001f;padding: 2px;border-radius: 7px;">'
                "{}</span>",
                logrecord_repr,
            )
            messages.success(self.request, message)

        return redirect("admin:operationsLog_logrecord_changelist")

    def not_confirm(self, id):
        logrecord = get_object_or_404(models.LogRecord, id=id)

        self.title = f"Отменить {logrecord}"

        context = self.get_context_data(
            logrecord=logrecord,
            revert_operation=REVERT_OPERATION_MESSAGES[logrecord.operation],
        )
        return self.render_to_response(context)


revert_logrecord = admin.site.admin_view(RevertLogRecordView.as_view())
