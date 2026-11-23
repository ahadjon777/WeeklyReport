from django.apps import AppConfig
from django.db.models.signals import post_migrate


def create_default_slots(sender, **kwargs):
    from .models import ReminderSlot

    if not ReminderSlot.objects.exists():
        import datetime as dt

        ReminderSlot.objects.bulk_create(
            [
                ReminderSlot(
                    time=dt.time(9, 0),
                    message="Ish kuni boshlandi. Bugungi ishlaringizni hisobotga kiritishni unutmang.",
                ),
                ReminderSlot(
                    time=dt.time(13, 0),
                    message="Kun yarmi o'tdi. Bajarilgan ishlarni hisobotga yozib qo'ying.",
                ),
                ReminderSlot(
                    time=dt.time(17, 0),
                    message="Ish kuni tugayapti. Bugungi hisobotni yakunlang.",
                ),
            ]
        )


def create_profile(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    from .models import Profile

    Profile.objects.get_or_create(user=instance)


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reports"
    verbose_name = "Hisobotlar"

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        post_migrate.connect(create_default_slots, sender=self)
        post_save.connect(create_profile, sender=get_user_model())
