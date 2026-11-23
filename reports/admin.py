from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Department, Profile, ReminderSlot, WorkEntry

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0


class HisobotUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "profile__department")


admin.site.unregister(User)
admin.site.register(User, HisobotUserAdmin)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(ReminderSlot)
class ReminderSlotAdmin(admin.ModelAdmin):
    list_display = ("time", "message", "active")
    list_editable = ("message", "active")


@admin.register(WorkEntry)
class WorkEntryAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "short_description", "hours", "status")
    list_filter = ("status", "date", "user__profile__department")
    search_fields = ("description", "user__username", "user__first_name", "user__last_name")
    date_hierarchy = "date"

    @admin.display(description="Ish")
    def short_description(self, obj):
        return obj.description[:70]
