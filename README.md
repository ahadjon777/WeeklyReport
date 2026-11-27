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

## Eslatmalar (kuniga 3 marta)
Standart vaqt: 09:00, 13:00, 17:00 (dushanba–juma). Xodim sahifani ochiq tutsa, shu vaqtda oyna chiqadi, ovoz eshitiladi va sarlavha miltillaydi. Vaqt va matnni `/admin/` > Eslatma vaqtlari bo'limida o'zgartirasiz.

## Sozlamalar (`config/settings.py`)
- `WORK_DAYS` — ish kunlari
- `BACKFILL_DAYS` — xodim necha kun orqaga yozuv kirita oladi (standart 3)

## Zaxira nusxa
Barcha ma'lumot bitta `db.sqlite3` faylda. Uni vaqti-vaqti bilan nusxalab qo'ying.
