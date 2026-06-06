from django.core.management.base import BaseCommand
from django.db import transaction

from apps.games.models import (
    AnagramGame,
    AnagramWord,
    QuizGame,
    QuizGameQuestion,
    QuizGameOption,
    GameDifficulty,
)


# ───────────────────────── ANAGRAMLAR ─────────────────────────
# O'zbekiston maktablari informatika fani atamalari.
# Har bir o'yin 5 ta so'zdan iborat: (so'z, ishora)
ANAGRAMS = [
    {
        "title": "Kompyuter Qurilmalari", "description": "Kompyuterning asosiy qurilmalari",
        "xp": 10, "difficulty": GameDifficulty.EASY, "order": 1,
        "words": [
            ("MONITOR", "Tasvirni ko'rsatuvchi qurilma"),
            ("PROTSESSOR", "Kompyuterning 'miyasi'"),
            ("KLAVIATURA", "Harf va raqam kiritish qurilmasi"),
            ("PRINTER", "Qog'ozga bosib chiqaruvchi qurilma"),
            ("SKANER", "Rasmni kompyuterga o'tkazuvchi qurilma"),
        ],
    },
    {
        "title": "Internet Olami", "description": "Internet va tarmoq atamalari",
        "xp": 10, "difficulty": GameDifficulty.EASY, "order": 2,
        "words": [
            ("INTERNET", "Jahon kompyuter tarmog'i"),
            ("BRAUZER", "Saytlarni ochuvchi dastur"),
            ("MODEM", "Internetga ulovchi qurilma"),
            ("TARMOQ", "O'zaro bog'langan kompyuterlar"),
            ("SERVER", "So'rovlarga xizmat qiluvchi kompyuter"),
        ],
    },
    {
        "title": "Dasturiy Ta'minot", "description": "Dasturlar va fayllar",
        "xp": 15, "difficulty": GameDifficulty.MEDIUM, "order": 3,
        "words": [
            ("DASTUR", "Buyruqlar ketma-ketligi"),
            ("WINDOWS", "Mashhur operatsion tizim"),
            ("ANTIVIRUS", "Viruslardan himoya dasturi"),
            ("FAYL", "Nom bilan saqlangan ma'lumot"),
            ("PAPKA", "Fayllar saqlanadigan jild"),
        ],
    },
    {
        "title": "Axborot va Kodlash", "description": "Axborot, xotira va o'lchov birliklari",
        "xp": 15, "difficulty": GameDifficulty.MEDIUM, "order": 4,
        "words": [
            ("AXBOROT", "Xabar, ma'lumot"),
            ("ALGORITM", "Amallar ketma-ketligi"),
            ("XOTIRA", "Ma'lumot saqlovchi qism"),
            ("BAYT", "8 bitdan iborat birlik"),
            ("PIKSEL", "Tasvirning eng kichik nuqtasi"),
        ],
    },
    {
        "title": "Murakkab Atamalar", "description": "Ilg'or informatika tushunchalari",
        "xp": 20, "difficulty": GameDifficulty.HARD, "order": 5,
        "words": [
            ("KOMPILYATOR", "Kodni mashina tiliga o'giruvchi"),
            ("PROTOKOL", "Aloqa qoidalari to'plami"),
            ("MEGABAYT", "Xotira o'lchov birligi"),
            ("GRAFIKA", "Tasvir bilan ishlash sohasi"),
            ("MULTIMEDIA", "Matn, ovoz va video birikmasi"),
        ],
    },
]


# ───────────────────────── KVIZLAR ─────────────────────────
# Har bir kviz 5 ta savol: (savol, [(variant, to'g'rimi), ...])
QUIZZES = [
    # ─────── OSON ───────
    {
        "title": "Informatika Asoslari", "description": "Boshlang'ich tushunchalar",
        "difficulty": GameDifficulty.EASY, "xp": 10, "order": 1,
        "questions": [
            ("Informatika fani nimani o'rganadi?",
             [("Axborot va uni qayta ishlashni", True), ("Faqat o'simliklarni", False), ("Tarix voqealarini", False), ("Faqat geometriyani", False)]),
            ("Quyidagilardan qaysi biri kiritish qurilmasi?",
             [("Klaviatura", True), ("Monitor", False), ("Printer", False), ("Kolonka", False)]),
            ("Sichqoncha (mouse) qanday vazifa bajaradi?",
             [("Kursorni boshqaradi", True), ("Matn chop etadi", False), ("Tovush chiqaradi", False), ("Rasm skanerlaydi", False)]),
            ("Monitor qanday qurilma hisoblanadi?",
             [("Chiqarish qurilmasi", True), ("Kiritish qurilmasi", False), ("Xotira qurilmasi", False), ("Tarmoq qurilmasi", False)]),
            ("Kompyuterning asosiy qurilmalaridan biri qaysi?",
             [("Protsessor", True), ("Stol", False), ("Ruchka", False), ("Daftar", False)]),
        ],
    },
    {
        "title": "Kompyuter Qurilmalari", "description": "Qurilmalar va ularning vazifasi",
        "difficulty": GameDifficulty.EASY, "xp": 10, "order": 2,
        "questions": [
            ("Protsessor kompyuterda qanday vazifani bajaradi?",
             [("Ma'lumotlarni qayta ishlaydi", True), ("Tovush chiqaradi", False), ("Rasm chizadi", False), ("Internetga ulaydi", False)]),
            ("Ma'lumotni doimiy saqlovchi qurilma qaysi?",
             [("Qattiq disk", True), ("Operativ xotira", False), ("Monitor", False), ("Klaviatura", False)]),
            ("Printer qanday qurilma?",
             [("Chiqarish qurilmasi", True), ("Kiritish qurilmasi", False), ("Hisoblash qurilmasi", False), ("Boshqarish qurilmasi", False)]),
            ("Klaviaturadagi eng uzun tugma qaysi?",
             [("Probel (bo'sh joy)", True), ("Enter", False), ("Shift", False), ("Esc", False)]),
            ("Quyidagilardan qaysi biri tashqi xotira hisoblanadi?",
             [("Flesh xotira", True), ("Protsessor", False), ("Monitor", False), ("Sichqoncha", False)]),
        ],
    },
    # ─────── O'RTA ───────
    {
        "title": "Operatsion Tizim va Fayllar", "description": "OT, fayl va papkalar",
        "difficulty": GameDifficulty.MEDIUM, "xp": 15, "order": 1,
        "questions": [
            ("Operatsion tizim nima?",
             [("Kompyuterni boshqaruvchi asosiy dastur", True), ("O'yin dasturi", False), ("Antivirus dasturi", False), ("Brauzer dasturi", False)]),
            ("Quyidagilardan qaysi biri operatsion tizim?",
             [("Windows", True), ("Word", False), ("Excel", False), ("Paint", False)]),
            ("Fayl nima?",
             [("Nom bilan saqlangan ma'lumotlar to'plami", True), ("Kompyuter qurilmasi", False), ("Klaviatura tugmasi", False), ("Tarmoq turi", False)]),
            ("Rasm fayli qaysi kengaytmaga ega bo'lishi mumkin?",
             [(".jpg", True), (".docx", False), (".mp3", False), (".exe", False)]),
            ("Papka (jild) nima uchun ishlatiladi?",
             [("Fayllarni tartibli saqlash uchun", True), ("Chop etish uchun", False), ("Internetga kirish uchun", False), ("Tovush eshitish uchun", False)]),
        ],
    },
    {
        "title": "Matn Muharriri (Word)", "description": "Microsoft Word bilan ishlash",
        "difficulty": GameDifficulty.MEDIUM, "xp": 15, "order": 2,
        "questions": [
            ("Microsoft Word dasturi nima uchun mo'ljallangan?",
             [("Matn hujjatlarini tayyorlash uchun", True), ("Rasm chizish uchun", False), ("Hisob-kitob uchun", False), ("Video montaj uchun", False)]),
            ("Matnni nusxalash uchun qaysi tugmalar birikmasi ishlatiladi?",
             [("Ctrl + C", True), ("Ctrl + V", False), ("Ctrl + X", False), ("Ctrl + P", False)]),
            ("Bajarilgan amalni bekor qilish (undo) uchun?",
             [("Ctrl + Z", True), ("Ctrl + S", False), ("Ctrl + A", False), ("Ctrl + B", False)]),
            ("Word hujjati odatda qaysi kengaytmaga ega?",
             [(".docx", True), (".xlsx", False), (".pptx", False), (".bmp", False)]),
            ("Nusxalangan matnni joylashtirish (paste) uchun?",
             [("Ctrl + V", True), ("Ctrl + C", False), ("Ctrl + Z", False), ("Ctrl + N", False)]),
        ],
    },
    {
        "title": "Internet va Tarmoqlar", "description": "Internet va elektron pochta",
        "difficulty": GameDifficulty.MEDIUM, "xp": 15, "order": 3,
        "questions": [
            ("Internet nima?",
             [("Jahon kompyuter tarmog'i", True), ("Bitta kompyuter", False), ("Operatsion tizim", False), ("Kiritish qurilmasi", False)]),
            ("Veb-saytlarni ko'rish uchun qaysi dastur ishlatiladi?",
             [("Brauzer", True), ("Kalkulyator", False), ("Paint", False), ("Bloknot", False)]),
            ("Quyidagilardan qaysi biri brauzer?",
             [("Google Chrome", True), ("Windows", False), ("Word", False), ("Excel", False)]),
            ("Elektron pochta manzilida qaysi belgi qatnashadi?",
             [("@", True), ("#", False), ("&", False), ("%", False)]),
            ("O'zbekiston saytlari ko'pincha qaysi domenda bo'ladi?",
             [(".uz", True), (".ru", False), (".us", False), (".eu", False)]),
        ],
    },
    {
        "title": "Algoritmlar", "description": "Algoritm va blok-sxemalar",
        "difficulty": GameDifficulty.MEDIUM, "xp": 15, "order": 4,
        "questions": [
            ("Algoritm nima?",
             [("Masalani yechish amallari ketma-ketligi", True), ("Kompyuter qurilmasi", False), ("Dastur nomi", False), ("Fayl turi", False)]),
            ("Algoritmni grafik tasvirlash usuli qanday ataladi?",
             [("Blok-sxema", True), ("Jadval", False), ("Diagramma", False), ("Grafik", False)]),
            ("Blok-sxemada shart (tanlash) qaysi shakl bilan belgilanadi?",
             [("Romb", True), ("To'rtburchak", False), ("Aylana", False), ("Uchburchak", False)]),
            ("Algoritmning boshlanishi va tugashi qaysi shakl bilan belgilanadi?",
             [("Oval", True), ("Romb", False), ("To'rtburchak", False), ("Strelka", False)]),
            ("Amallar ma'lum shartga ko'ra qayta-qayta bajarilsa, bu qanday algoritm?",
             [("Takrorlanuvchi (siklik)", True), ("Chiziqli", False), ("Tarmoqlanuvchi", False), ("Yordamchi", False)]),
        ],
    },
    # ─────── QIYIN ───────
    {
        "title": "Sanoq Sistemalari", "description": "Ikkilik sanoq sistemasi va o'lchov birliklari",
        "difficulty": GameDifficulty.HARD, "xp": 20, "order": 1,
        "questions": [
            ("Kompyuter qaysi sanoq sistemasida ishlaydi?",
             [("Ikkilik (binar)", True), ("O'nlik", False), ("Sakkizlik", False), ("O'n oltilik", False)]),
            ("Ikkilik sanoq sistemasida nechta raqam ishlatiladi?",
             [("2 ta (0 va 1)", True), ("8 ta", False), ("10 ta", False), ("16 ta", False)]),
            ("1 bayt necha bitdan iborat?",
             [("8", True), ("2", False), ("4", False), ("16", False)]),
            ("10 (o'nlik) soni ikkilik sistemada qanday yoziladi?",
             [("1010", True), ("1100", False), ("1001", False), ("1110", False)]),
            ("1 Kilobayt (KB) necha baytga teng?",
             [("1024", True), ("1000", False), ("512", False), ("256", False)]),
        ],
    },
    {
        "title": "Dasturlash Asoslari", "description": "Dasturlash tushunchalari",
        "difficulty": GameDifficulty.HARD, "xp": 20, "order": 2,
        "questions": [
            ("Dasturlash tili nima uchun kerak?",
             [("Kompyuterga buyruq berish uchun", True), ("Rasm chizish uchun", False), ("Musiqa tinglash uchun", False), ("Internetga kirish uchun", False)]),
            ("Quyidagilardan qaysi biri dasturlash tili?",
             [("Python", True), ("Windows", False), ("Chrome", False), ("Word", False)]),
            ("O'zgaruvchi (variable) nima?",
             [("Qiymat saqlovchi nom", True), ("Kompyuter qurilmasi", False), ("Operatsion tizim", False), ("Tarmoq turi", False)]),
            ("Shartga ko'ra amal bajarish qaysi operator orqali amalga oshiriladi?",
             [("if", True), ("for", False), ("print", False), ("input", False)]),
            ("Dasturdagi xatolik (nosozlik) qanday ataladi?",
             [("Bag (bug)", True), ("Fayl", False), ("Papka", False), ("Drayver", False)]),
        ],
    },
]


class Command(BaseCommand):
    help = "Informatika fani bo'yicha anagram va kviz o'yinlarini yaratadi (idempotent)"

    @transaction.atomic
    def handle(self, *args, **options):
        # Seedda yo'q eski o'yinlarni tozalaymiz (avtoritativ holat)
        anagram_titles = [a["title"] for a in ANAGRAMS]
        quiz_titles = [q["title"] for q in QUIZZES]
        AnagramGame.objects.exclude(title__in=anagram_titles).delete()
        QuizGame.objects.exclude(title__in=quiz_titles).delete()

        anagram_count, word_count = 0, 0
        for data in ANAGRAMS:
            words = data.pop("words")
            game, _ = AnagramGame.objects.update_or_create(
                title=data["title"], defaults=data,
            )
            game.words.all().delete()
            for w_order, (text, hint) in enumerate(words, start=1):
                AnagramWord.objects.create(game=game, text=text, hint=hint, order=w_order)
                word_count += 1
            anagram_count += 1

        quiz_count, q_count = 0, 0
        for data in QUIZZES:
            questions = data.pop("questions")
            quiz, _ = QuizGame.objects.update_or_create(
                title=data["title"], defaults=data,
            )
            quiz.questions.all().delete()
            for q_order, (text, options) in enumerate(questions, start=1):
                question = QuizGameQuestion.objects.create(quiz=quiz, text=text, order=q_order)
                for opt_text, is_correct in options:
                    QuizGameOption.objects.create(question=question, text=opt_text, is_correct=is_correct)
                q_count += 1
            quiz_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor! {anagram_count} ta anagram ({word_count} ta so'z), "
            f"{quiz_count} ta kviz ({q_count} ta savol) yaratildi/yangilandi."
        ))
