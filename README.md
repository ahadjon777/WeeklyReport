# WeeklyReport

Xodimlar kunlik ishlarini kiritadi. Rahbar hafta, oy, chorak, yarim yil va yil bo'yicha yig'ma hisobot oladi va Excel'ga yuklaydi. Internet kerak emas, faqat lokal tarmoq.

## O'rnatish (bir marta, Windows)
1. Python 3.10+ o'rnating (o'rnatishda "Add Python to PATH" belgilang).
2. `setup.bat` ni ikki marta bosing, rahbar uchun login va parol kiriting.
3. `run.bat` ni ikki marta bosing. Oynada chiqqan manzilni (masalan `http://192.168.1.10:8000`) xodimlarga bering.

Kompyuter yoqilgan va `run.bat` ochiq turganda tizim ishlaydi. Windows xavfsizlik oynasi chiqsa, "Ruxsat berish" (Private network) ni bosing.

## Boshqaruv paneli (rahbar uchun)
Rahbar kirganda `/boshqaruv/` sahifasi ochiladi: bugungi holat, hisobot bermaganlar, 14 kunlik grafik, bo'limlar kesimi. Chap menyuda:
- **Xodimlar** — qidirish, qo'shish, tahrirlash, parolni tiklash, o'chirish (hisobotlari saqlanadi)
- **Bo'limlar** — qo'shish, nomini o'zgartirish
- **Eslatmalar** — kuniga 3 ta vaqt va matn
- **Ommaviy import** — `.xlsx` yoki `.csv` fayl yuklab, 40-50 xodimni bir bosishda qo'shish (parollar ekranda ko'rinadi, CSV qilib yuklab olinadi)

## Soat ixtiyoriy
Xodim ish soatini yozishi shart emas. Soat bo'sh qolsa, hisobotlarda yozuvlar soni asosiy ko'rsatkich bo'ladi. Hech kim soat kiritmagan davrda hisobotlarda (sayt, Word) soat ustuni umuman chiqmaydi.

## Word hisobot
«Yig'ma hisobotlar» sahifasida **Word hisobot (.docx)** tugmasi: hafta, oy, chorak, yarim yil yoki yil uchun tayyor shablon (sarlavha, umumiy ko'rsatkichlar, xodimlar jadvali, bajarilgan ishlar, imzo joylari). Bo'lim yoki xodim tanlab, faqat shuni ham chiqarish mumkin. Tashkilot nomi `config/settings.py` dagi `ORG_NAME` da o'zgartiriladi.

## Xodimlarni qo'shish
- **Ommaviy:** `xodimlar.csv` ni to'ldiring (faqat `full_name` majburiy) va `import_employees.bat` ni bosing. Login va parollar `parollar.csv` ga yoziladi.
- **Yakka:** brauzerda `/admin/` > Foydalanuvchilar.

## Eslatma dasturi (brauzer yopiq bo'lsa ham)
Eslatma har bir xodimning kompyuterida alohida kichik dastur orqali chiqadi (`agent` papkasi). Standart vaqt: **11:00, 16:00, 19:00** (dushanba–juma). Vaqtni rahbar panelidagi «Eslatmalar» bo'limida o'zgartirasiz, dasturlar o'zi yangilanadi.

**Bir marta tayyorlash (Python o'rnatilgan kompyuterda, masalan sizniki):**
1. `agent\server.txt` ga server manzilini yozing, masalan `http://192.168.1.10:8000`.
2. `agent\build_agent.bat` ni bosing, `weekly_agent.exe` yaratiladi.

**Har bir xodim kompyuteriga o'rnatish (1 daqiqa):**
1. `agent` papkasini (kamida `weekly_agent.exe`, `install_agent.bat`, `server.txt`) flesh yoki umumiy papka orqali nusxalang.
2. `install_agent.bat` ni ikki marta bosing va shu xodimning **loginini** kiriting.
3. Sinov eslatma oynasi chiqadi. Shundan keyin dastur kompyuter yoqilganda o'zi ishga tushadi.

Olib tashlash: `uninstall_agent.bat`. Dastur jurnali: `%LOCALAPPDATA%\WeeklyReport\agent.log`.

Muhim:
- Server kompyuterining IP manzili o'zgarmasligi kerak (routerda shu kompyuterga doimiy IP bering), aks holda dastur serverni topa olmaydi.
- Kompyuter kech yoqilsa, eng oxirgi o'tgan eslatma 3 soat ichida ko'rsatiladi.
- `config/settings.py` da: `REMIND_ONLY_IF_NO_REPORT = True` qilsangiz, bugun hisobot kiritgan xodimga eslatma chiqmaydi; `BROWSER_REMINDERS = False` qilsangiz, sayt ichidagi eslatma o'chadi (dastur o'rnatilgan bo'lsa, takrorlanmasligi uchun).

## Eslatmalar (kuniga 3 marta)
Standart vaqt: 11:00, 16:00, 19:00 (dushanba–juma). Xodim sahifani ochiq tutsa, shu vaqtda oyna chiqadi, ovoz eshitiladi va sarlavha miltillaydi. Vaqt va matnni `/admin/` > Eslatma vaqtlari bo'limida o'zgartirasiz.

## Sozlamalar (`config/settings.py`)
- `WORK_DAYS` — ish kunlari
- `BACKFILL_DAYS` — xodim necha kun orqaga yozuv kirita oladi (standart 3)

## Portni o'zgartirish
Standart port 8000. Boshqa port kerak bo'lsa, loyiha papkasida `cmd` oching va yozing (masalan 8080 uchun):
```
echo 8080>port.txt
```
Keyin `run.bat` ni qayta ishga tushiring. Standart portga qaytish uchun `del port.txt`. Brandmauerda yangi portga ruxsat bering va eslatma dasturidagi `server.txt` ga yangi manzilni yozing.

## Internetsiz tarmoqqa ko'chirish
Internet bor kompyuterda (loyiha ishlayotgan joyda):
1. `offline_tayyorlash.bat` ni bosing, kutubxonalar `wheels` papkasiga yuklanadi. Oxirida chiqqan **Python versiyasini** yozib oling (masalan 3.13.1).
2. python.org dan **aynan shu versiyadagi** Windows installer ni (`Windows installer (64-bit)`) yuklab oling.
3. Flesh-diskka quyidagilarni nusxalang: butun `WeeklyReport` papkasi (ichida `wheels` bor, lekin **`venv` papkasi va `db.sqlite3` siz**) va Python installer.

Internetsiz tarmoqdagi server kompyuterida:
1. Python installer ni ishga tushiring, **Add Python to PATH** ni belgilab o'rnating.
2. `setup.bat` ni bosing (kutubxonalar `wheels` dan o'rnatiladi) va rahbar logini/parolini kiriting.
3. `xodimlar.csv` ni to'ldirib, `import_employees.bat` ni bosing (yoki panelda «Ommaviy import»).
4. `run.bat` ni bosing, oynadagi manzilni xodimlarga bering.
5. Server kompyuteriga doimiy IP bering va brandmauerda 8000 portga ruxsat bering.
6. Eslatma dasturi: `agent\server.txt` ga yangi server manzilini yozing, `agent` papkasini xodimlar kompyuteriga nusxalab `install_agent.bat` ni bosing (`weekly_agent.exe` ni oldindan yaratgan bo'lishingiz kerak, xodimlar kompyuterida Python kerak emas).

Eski ma'lumotlarni ham olib o'tmoqchi bo'lsangiz, `db.sqlite3` ni ham nusxalang (sinov yozuvlari ham o'tadi, shuning uchun odatda yangidan boshlash yaxshiroq).

## Zaxira nusxa
Barcha ma'lumot bitta `db.sqlite3` faylda. Uni vaqti-vaqti bilan nusxalab qo'ying.
