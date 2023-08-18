from django.urls import path

from . import views

app_name = "operationsLog"
urlpatterns = [
    path("logrecord/<uuid:id>/revert/", views.revert_logrecord, name="logrecord-revert"),
]
