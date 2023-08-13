from django.urls import path

from . import views

app_name = "operationsLog"
urlpatterns = [
    path("revert/<uuid:id>/", views.revert_logrecord, name="logrecord-revert"),
]
