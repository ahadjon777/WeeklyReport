import datetime as dt

from django.db import migrations


def forwards(apps, schema_editor):
    """Faqat eski standart vaqtlar (9, 13, 17) o'zgartirilmagan bo'lsa, 11, 16, 19 ga o'tkazadi."""
    Slot = apps.get_model("reports", "ReminderSlot")
    slots = list(Slot.objects.order_by("time"))
    old = [dt.time(9, 0), dt.time(13, 0), dt.time(17, 0)]
    if [s.time for s in slots] == old:
        for s, t in zip(slots, [dt.time(11, 0), dt.time(16, 0), dt.time(19, 0)]):
            s.time = t
            s.save()


class Migration(migrations.Migration):
    dependencies = [("reports", "0002_hours_optional")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
