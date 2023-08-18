from django.urls import path

from . import views

app_name = "readersRecords"
admin_urlpatterns = [
    path("import/", views.import_readers, name="readers-import"),
    path("export/", views.export_readers, name="readers-export"),
    path("update_grade/", views.update_students_grade, name="readers-update-grade"),
    path("change_group/", views.change_students_group, name="readers-change-group"),
]
