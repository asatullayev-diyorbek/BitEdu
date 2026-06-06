# 🎮 Implementation Reja: "O'yinlar" (Games) moduli — EduPlatform

> Rasmlardagi **Anagram O'yinlari** va **Quiz O'yinlari** ni mavjud loyihaga
> (Django REST + React) qo'shish uchun to'liq texnik reja. Loyihaning hozirgi
> arxitekturasiga (UUID PK, DRF `APIView`, `StandardPagination`, wrapper
> response `{status, message, data}`, JWT, `StudentProfile.total_points`,
> admin CRUD patternlari) **to'liq mos** holda yozildi.

---

## 1. Rasmlar tahlili (nimani quramiz)

Skrinshotlardan ikki xil mustaqil o'yin turi ko'rinadi:

### 1.1. Anagram O'yinlari (Rasm 1–3)
- Karta grid: har bir o'yin = **sarlavha**, **tavsif**, **XP** (27, 10, 10...), **necha marta o'ynalgani** ("2 marta o'ynalgan"), **"O'ynash"** tugmasi.
- O'yin ekrani: aralashtirilgan harflar bloklari (`L B I V R A A E`) → pastdagi **"Harflarni bu yerga sudrang"** drop-zonasiga drag&drop qilib so'z yig'iladi → **"Tekshirish"** / **"Qayta boshlash"**.
- Tugatilgan holat banneri: ✅ *"Siz bu o'yinni allaqachon bajargansiz! Ball: 27 XP | Urinishlar: 1 — Qayta bajarish mumkin, lekin ball qo'shilmaydi."*
- **Xulosa:** har o'yin bitta yashirin so'zga ega. To'g'ri yiqsa XP beriladi (faqat birinchi marta).

### 1.2. Quiz O'yinlari (Rasm 4–6)
- Qiyinlik tanlash ekrani: **Oson** (yashil) / **O'rta** (sariq) / **Qiyin** (qizil) — har biri "Savollar mavjud" badge.
- Qiyinlik tanlangach kvizlar ro'yxati: "Python O'rta - 5" (String metodlari), "Python O'rta - 4" (Sikl operatorlari)... har birida **15 XP**, **necha marta o'ynalgani**, **"O'ynash"**.
- Kviz ekrani: bitta savol + 4 variant (rangli kartalar) → **"Tekshirish"**.

> ⚠️ Eslatma: loyihada allaqachon `apps.tests` (Topic'ga bog'langan testlar) bor.
> Bu **boshqa narsa** — o'yinlar Topic'dan mustaqil, qiyinlik bo'yicha
> guruhlanadi va o'zining XP/urinish hisobini yuritadi. Shu sababli alohida
> `apps.games` app ochamiz, mavjud `tests` ni buzmaymiz.

---

## 2. Backend: `apps.games` app

### 2.1. App yaratish
```bash
cd backend
python manage.py startapp games apps/games
```
`config/settings.py` → `INSTALLED_APPS` ga qo'shish:
```python
'apps.games',
```
`config/urls.py` ga qo'shish:
```python
path('api/v1/games/', include('apps.games.api.urls')),
```

### 2.2. Modellar — `apps/games/models.py`

Mavjud konvensiyalar saqlanadi: `UUIDField` PK, `created_at`, `StudentProfile`
bilan FK, `is_active`, `ordering`.

```python
import uuid
from django.db import models
from django.utils import timezone
from apps.users.models import StudentProfile


class GameDifficulty(models.TextChoices):
    EASY = "EASY", "Oson"
    MEDIUM = "MEDIUM", "O'rta"
    HARD = "HARD", "Qiyin"


# ─────────────────────────── ANAGRAM ───────────────────────────
class AnagramGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)              # "Python Asoslari"
    description = models.CharField(max_length=512, blank=True)  # "...savollar"
    answer = models.CharField(max_length=64)              # yashirin so'z, masalan "VARIABLE"
    hint = models.CharField(max_length=255, blank=True)   # ixtiyoriy ishora
    xp = models.PositiveIntegerField(default=10)          # to'g'ri yechgan uchun XP
    difficulty = models.CharField(
        max_length=10, choices=GameDifficulty.choices,
        default=GameDifficulty.EASY,
    )
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.title} ({self.answer})"

    @property
    def scrambled_letters(self):
        """Javobni serverda emas, frontda aralashtiramiz; bu faqat uzunlik/harf to'plami."""
        return list(self.answer.upper())


# ─────────────────────────── QUIZ ───────────────────────────
class QuizGame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)              # "Python O'rta - 5"
    description = models.CharField(max_length=512, blank=True)  # "String metodlari"
    difficulty = models.CharField(
        max_length=10, choices=GameDifficulty.choices,
        default=GameDifficulty.MEDIUM, db_index=True,
    )
    xp = models.PositiveIntegerField(default=15)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["difficulty", "order"]

    def __str__(self):
        return f"{self.title} [{self.difficulty}]"


class QuizGameQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(QuizGame, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()                              # "Matnni katta harflarga..."
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = ("quiz", "order")


class QuizGameOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(QuizGameQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)               # "upper()"
    is_correct = models.BooleanField(default=False)


# ───────────────── O'YIN URINISHLARI (umumiy) ─────────────────
class GameAttempt(models.Model):
    """Anagram ham, Quiz ham shu yerda; generic emas — 2 ta nullable FK."""
    class GameType(models.TextChoices):
        ANAGRAM = "ANAGRAM", "Anagram"
        QUIZ = "QUIZ", "Quiz"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="game_attempts"
    )
    game_type = models.CharField(max_length=10, choices=GameType.choices, db_index=True)
    anagram = models.ForeignKey(AnagramGame, on_delete=models.CASCADE, null=True, blank=True)
    quiz = models.ForeignKey(QuizGame, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)        # to'liq to'g'ri bajarildimi
    points_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student_profile", "game_type"]),
        ]
```

> **Ball berish qoidasi (rasmga mos):** o'yin **birinchi marta to'g'ri**
> bajarilganda XP `StudentProfile.total_points` ga qo'shiladi. Keyingi
> urinishlarda `points_awarded=0` (banner: *"Qayta bajarish mumkin, lekin ball
> qo'shilmaydi"*). "Necha marta o'ynalgan" = shu o'yin bo'yicha `GameAttempt`
> soni.

### 2.3. Serializerlar — `apps/games/api/serializers.py`

- `AnagramGameListSerializer` → `id, title, description, xp, difficulty, played_count, is_completed` (javob **bermaydi**).
- `AnagramGameDetailSerializer` → yuqoridagi + `scrambled_letters` (harflar ro'yxati), `answer_length`. **`answer` hech qachon chiqmaydi.**
- `AnagramSubmitSerializer` → `{ "answer": "VARIABLE" }` qabul qiladi.
- `QuizGameListSerializer` → `id, title, description, xp, difficulty, played_count, is_completed`.
- `QuizGameDetailSerializer` → questions + options (lekin `is_correct` **chiqmaydi**).
- `QuizSubmitSerializer` → `{ "answers": [{question_id, selected_option_id}] }`.
- `GameResultSerializer` → `{ is_correct, correct, points_awarded, already_completed, attempts_count, total_points }` (Anagram/Quiz natija ekrani uchun).

`played_count` / `is_completed` ni har bir o'quvchi uchun
`SerializerMethodField` orqali yoki `views`da `annotate`/`prefetch` bilan
hisoblang (N+1 dan qochish uchun `views` darajasida tayyorlab uzating).

### 2.4. Views — `apps/games/api/views.py`

`apps/tests/api/views.py` dagi `StudentOnlyAPIView` patternини qayta ishlating
(role tekshiruvi + `student_profile` olish). Endpointlar:

**Student:**
- `GET  /api/v1/games/anagrams/` — ro'yxat (`played_count`, `is_completed` bilan), `StandardPagination`.
- `GET  /api/v1/games/anagrams/<uuid:id>/` — o'yin detali (scrambled harflar).
- `POST /api/v1/games/anagrams/<uuid:id>/submit/` — javobni tekshirish + ball berish.
- `GET  /api/v1/games/quizzes/?difficulty=MEDIUM` — qiyinlik bo'yicha kvizlar.
- `GET  /api/v1/games/quizzes/difficulties/` — `[{key:EASY,label:"Oson",count:N}, ...]` (qiyinlik tanlash ekrani uchun).
- `GET  /api/v1/games/quizzes/<uuid:id>/` — kviz savollari + variantlari.
- `POST /api/v1/games/quizzes/<uuid:id>/submit/` — javoblarni tekshirish + ball.

**Submit logikasi (ikkalasi uchun umumiy yordamchi):**
```python
PASS = to'liq to'g'ri (anagram: answer == game.answer; quiz: barcha javob to'g'ri)
with transaction.atomic():
    already = GameAttempt.objects.filter(
        student_profile=profile, game_type=..., <fk>=game, is_correct=True
    ).exists()
    points = game.xp if (is_correct and not already) else 0
    GameAttempt.objects.create(..., is_correct=is_correct, points_awarded=points)
    if points:
        profile.total_points = F('total_points') + points  # leaderboardга qo'shiladi
        profile.save(update_fields=['total_points'])
    attempts_count = GameAttempt.objects.filter(student_profile=profile, <fk>=game).count()
return GameResultSerializer({...})
```
Bu mavjud `TestSubmissionAPIView` bilan bir xil uslubda (atomic, `total_points`
yangilash) — leaderboard avtomatik ishlaydi, alohida ish kerak emas.

**Admin (CRUD) — `tests/admin/...` patterniga mos:**
- `AnagramGame` ListCreate / RetrieveUpdateDestroy (`generics`, `IsAuthenticated` + role=ADMIN).
- `QuizGame` (+nested savol/variant yozish, `AdminTestQuestionSerializer` dagi nested-create uslubida).

### 2.5. Admin panel — `apps/games/admin.py`
`AnagramGame`, `QuizGame` (inline `QuizGameQuestion` → inline `QuizGameOption`),
`GameAttempt` (read-only) ni `admin.site.register` qiling — kontent kiritish uchun.

### 2.6. Migratsiya + boshlang'ich data
```bash
python manage.py makemigrations games
python manage.py migrate
```
`apps/games/management/commands/seed_games.py` — rasmlardagi namunaviy o'yinlarni
yaratuvchi seed (Python Asoslari → "VARIABLE", "Python O'rta - 5" → String
metodlari kvizi va h.k.). Demo va test uchun.

---

## 3. Frontend: React sahifalari

Mavjud patternlar: `src/api/axios.js` (token + wrapper xato ushlash),
`react-router-dom` v7, `react-hot-toast`, `lucide-react`, Tailwind v4.
Wrapper javob `res.data?.data?.results` ko'rinishida o'qiladi (StudentQuiz'dagi
kabi).

> 🎨 **Dizayn eslatmasi:** rasmlar **qorong'i (dark)** mavzuda — mavjud student
> panel esa oq. Shuning uchun o'yinlar uchun alohida dark konteyner
> (`bg-[#0b1120]` / gradient) ishlatamiz, lekin layout (`StudentLayout`,
> sidebar) o'sha-o'sha qoladi. Kartalardagi binafsha gradient tugma
> (`O'ynash`), XP badge, glow effektlar Tailwind bilan beriladi.

### 3.1. Routing — `src/App.jsx` ga qo'shish
```jsx
<Route path="games" element={<GamesHome />} />                 {/* O'yinlar bo'limi */}
<Route path="games/anagram" element={<AnagramList />} />
<Route path="games/anagram/:id" element={<AnagramPlay />} />
<Route path="games/quiz" element={<QuizDifficulty />} />        {/* Oson/O'rta/Qiyin */}
<Route path="games/quiz/:difficulty" element={<QuizList />} />
<Route path="games/quiz/play/:id" element={<QuizPlay />} />
```
`StudentLayout.jsx` → `MENU` massiviga qo'shish:
```js
{ icon: Gamepad2, label: "O'yinlar", path: '/student/games' },
```

### 3.2. Yangi fayllar — `src/pages/student/games/`

| Fayl | Vazifasi | Mos rasm |
|---|---|---|
| `GamesHome.jsx` | Ikki katta karta: "Anagram O'yinlari" / "Quiz O'yinlari" | — (hub) |
| `AnagramList.jsx` | Anagram o'yinlari grid (XP, "N marta o'ynalgan", O'ynash) | Rasm 1 |
| `AnagramPlay.jsx` | Drag&drop harflar + drop-zona + Tekshirish/Qayta boshlash + tugatilgan banner | Rasm 2–3 |
| `QuizDifficulty.jsx` | Oson/O'rta/Qiyin tanlash kartalari (yashil/sariq/qizil) | Rasm 4 |
| `QuizList.jsx` | Tanlangan qiyinlikdagi kvizlar grid + "← Orqaga" | Rasm 6 |
| `QuizPlay.jsx` | Savol + 4 rangli variant karta + Tekshirish | Rasm 5 |

### 3.3. `AnagramPlay.jsx` — drag&drop yondashuvi
- API'dan `scrambled_letters` (yoki frontда `answer_length` bo'yicha) keladi.
- Ikki ro'yxat state: `tray` (yuqori, aralash harflar) va `slot` (drop-zona).
- **Native HTML5 drag&drop** (`draggable`, `onDragStart`, `onDrop`, `onDragOver`)
  — qo'shimcha kutubxona shart emas. Mobil uchun **tap-to-place** fallback (harfga
  bosilsa slotга tushadi) qo'shilsa yaxshi.
- "Tekshirish" → `slot` harflari birlashtirib `POST .../submit/ { answer }`.
- Natija: to'g'ri bo'lsa ✅ banner + `+XP` toast; allaqachon bajarilgan bo'lsa
  "ball qo'shilmaydi" matni (API `already_completed` flagidan).
- "Qayta boshlash" → harflarni `tray` ga qaytarib, qayta aralashtirish.

### 3.4. `QuizPlay.jsx`
- `StudentQuiz.jsx` ni shablon sifatida oling (allaqachon variant tanlash,
  submit, natija ekrani bor) — faqat endpointlar `games/quizzes/...` ga
  o'zgaradi va dark dizaynга moslanadi.
- Variant kartalari rasmga mos rangli (ko'k/qizil/to'q sariq/yashil) — bu shunchaki
  dekorativ, `is_correct` faqat submit javobida ko'rsatiladi.

### 3.5. Reusable komponentlar
- `GameCard.jsx` — sarlavha, tavsif, XP badge, "N marta o'ynalgan", O'ynash tugmasi
  (Anagram & Quiz ro'yxatlarида ishlatiladi).
- `XpBadge.jsx`, `CompletedBanner.jsx` — takrorlanmaslik uchun.

---

## 4. Gamifikatsiya integratsiyasi (TZ §5 ga mos)
- O'yin XP'lari `StudentProfile.total_points` ga tushadi → **mavjud leaderboard**
  (`/api/v1/results/leaderboard/`) avtomatik ularni hisobga oladi. Qo'shimcha kod yo'q.
- TZ'dagi **Badges** ("Tezkor", "Bilimdon") kelajakda `GameAttempt` statistikasi
  asosida berilishi mumkin (masalan 10 ta anagram → "Bilimdon"). Bu rejaning
  **2-fazasi** (ixtiyoriy).

---

## 5. Bajarish tartibi (bosqichlar)

1. **Backend modellar** — `apps/games` app, modellar, migratsiya. ✅ asos
2. **Backend serializer + student viewlar** — list/detail/submit (Anagram → keyin Quiz).
3. **Admin CRUD + admin.py + seed_games** — kontent kiritish imkoni.
4. **Frontend routing + menyu + `GamesHome`**.
5. **Anagram frontend** — list → drag&drop play → natija.
6. **Quiz frontend** — difficulty → list → play → natija.
7. **Sayqal** — dark dizayn, glow, mobil tap fallback, toast'lar, bo'sh holatlar.
8. **(Faza 2)** Badges, animatsiyalar, statistika.

---

## 6. Asosiy fayllar ro'yxati (yangi/o'zgaradigan)

**Backend (yangi):**
- `apps/games/models.py`, `admin.py`, `apps.py`
- `apps/games/api/{serializers,views,urls}.py`
- `apps/games/management/commands/seed_games.py`
- `apps/games/migrations/0001_initial.py`

**Backend (tahrir):**
- `config/settings.py` (INSTALLED_APPS)
- `config/urls.py` (games route)

**Frontend (yangi):**
- `src/pages/student/games/{GamesHome,AnagramList,AnagramPlay,QuizDifficulty,QuizList,QuizPlay}.jsx`
- `src/components/student/games/{GameCard,XpBadge,CompletedBanner}.jsx`

**Frontend (tahrir):**
- `src/App.jsx` (routelar)
- `src/components/student/StudentLayout.jsx` (menyuga "O'yinlar")

---

## 7. Xavfsizlik / sifat eslatmalari
- **Anagram `answer` va Quiz `is_correct` hech qachon GET javobida chiqmasligi**
  kerak (aks holda o'yin ma'nosi yo'qoladi) — serializerlarda qat'iy nazorat.
- Submit endpointlari **faqat STUDENT** roli uchun (mavjud `StudentOnlyAPIView`).
- Ball berishda `transaction.atomic` + `F()` (race conditionдан himoya), aynan
  `TestSubmissionAPIView` kabi.
- `played_count`/`is_completed` ni `views`da `prefetch`/`annotate` bilan
  hisoblab N+1 ни oldini oling.
