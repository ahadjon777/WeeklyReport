from django.contrib.auth import views as auth_views
from django.urls import path

from . import staff_views as sv
from . import views

urlpatterns = [
    # Boshqaruv paneli
    path("boshqaruv/", sv.dashboard, name="panel"),
    path("boshqaruv/xodimlar/", sv.employees, name="panel_employees"),
    path("boshqaruv/xodimlar/yangi/", sv.employee_edit, name="panel_employee_new"),
    path("boshqaruv/xodimlar/<int:pk>/", sv.employee_edit, name="panel_employee_edit"),
    path("boshqaruv/xodimlar/<int:pk>/parol/", sv.employee_reset_password, name="panel_employee_password"),
    path("boshqaruv/xodimlar/<int:pk>/holat/", sv.employee_toggle, name="panel_employee_toggle"),
    path("boshqaruv/bolimlar/", sv.departments, name="panel_departments"),
    path("boshqaruv/eslatmalar/", sv.reminders, name="panel_reminders"),
    path("boshqaruv/import/", sv.import_page, name="panel_import"),
    path("boshqaruv/import/shablon/", sv.import_sample, name="panel_import_sample"),
    path("", views.my_entries, name="my_entries"),
    path("yozuv/<int:pk>/tahrirlash/", views.entry_edit, name="entry_edit"),
    path("yozuv/<int:pk>/ochirish/", views.entry_delete, name="entry_delete"),
    path("hisobot/", views.summary, name="summary"),
    path("hisobot/excel/", views.export_excel, name="export_excel"),
    path("hisobot/word/", views.export_word, name="export_word"),
    path("eslatma/tekshir/", views.reminder_check, name="reminder_check"),
    path("eslatma/yopish/", views.reminder_ack, name="reminder_ack"),
    path("eslatma/api/", views.agent_schedule, name="agent_schedule"),
    path(
        "kirish/",
        views.StaffAwareLoginView.as_view(template_name="reports/login.html"),
        name="login",
    ),
    path("chiqish/", auth_views.LogoutView.as_view(), name="logout"),
]
