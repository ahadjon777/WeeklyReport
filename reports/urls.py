from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.my_entries, name="my_entries"),
    path("yozuv/<int:pk>/tahrirlash/", views.entry_edit, name="entry_edit"),
    path("yozuv/<int:pk>/ochirish/", views.entry_delete, name="entry_delete"),
    path("hisobot/", views.summary, name="summary"),
    path("hisobot/excel/", views.export_excel, name="export_excel"),
    path("eslatma/tekshir/", views.reminder_check, name="reminder_check"),
    path("eslatma/yopish/", views.reminder_ack, name="reminder_ack"),
    path(
        "kirish/",
        auth_views.LoginView.as_view(template_name="reports/login.html"),
        name="login",
    ),
    path("chiqish/", auth_views.LogoutView.as_view(), name="logout"),
]
