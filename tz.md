# 📝 Texnik Topshiriq: "EduPlatform" – Gamifikatsiyalashgan O‘quv Tizimi

## 1. Loyiha haqida qisqacha

7–11 sinf o‘quvchilari uchun mo‘ljallangan, darslar, video materiallar va testlar orqali bilim beruvchi interfaol platforma. Tizimda o‘quvchilar reyting orqali o‘zaro musobaqalashadi.

---

## 2. Texnologik Stek (Tavsiya)

- **Backend:** Python (Django + Django REST Framework)  
- **Frontend:** React.js yoki Vue.js (SPA arxitekturasi)  
- **Ma’lumotlar bazasi:** PostgreSQL  
- **Kesh / Real-time:** Redis (Reyting uchun) yoki oddiy DB queries  
- **Storage:** AWS S3 yoki DigitalOcean Spaces (Video va PDFlar uchun)  

---

## 3. Backend (Django) Talablari

### 3.1. Foydalanuvchilar iyerarxiyasi (Auth)

- **Admin:** Tizim sozlamalari, fanlar va sinflarni boshqarish  
- **O‘qituvchi (Ustoz):**  
  - Mavzu yuklash  
  - Video/material biriktirish  
  - Test savollarini kiritish  
  - O‘z sinfi statistikasini ko‘rish  
- **O‘quvchi:**  
  - Profil egasi  
  - Darslarni o‘zlashtirish  
  - Test yechish  
  - Ball yig‘ish  

---

### 3.2. Ma’lumotlar Strukturasi (Models)

- **Grades:** 7-dan 11-sinfgacha bo‘lgan toifalar  
- **Subjects:** Fanlar nomi (masalan: Informatika)  
- **Topics (Mavzular):**
  - Sarlavha  
  - Matnli kontent  
  - Video darslik (File/URL)  
  - Qo‘shimcha materiallar (PDF, Docs)  

- **Tests:**  
  - Har bir mavzuga bog‘langan 5–10 ta test  
  - Savol  
  - Variantlar  
  - To‘g‘ri javob flagi  

- **Results & Leaderboard:**  
  - O‘quvchining har bir darsdan olgan bali  
  - Umumiy ballar jamg‘armasi  

---

### 3.3. API Endpointlar

- `/api/v1/auth/` – Login/Register  
- `/api/v1/lessons/?grade=9&subject=it` – Filtrlangan darslar ro‘yxati  
- `/api/v1/test/submit/` – Test javoblarini qabul qilish va ball hisoblash  
- `/api/v1/leaderboard/?grade=9` – Sinf kesimidagi reyting  

---

## 4. Frontend Talablari

### 4.1. Dizayn va UX

- **Dashboard:** O‘quvchi uchun "Learning Path" (Xarita ko‘rinishidagi darslar ketma-ketligi)  
- **Responsive Design:** Telefon, planshet va kompyuterga to‘liq moslashuvchanlik  
- **PWA:** Saytni mobil ilova sifatida o‘rnatish imkoniyati (Manifest.json & Service Workers)  

---

### 4.2. Asosiy sahifalar

- **Landing Page:** Kirish va tanlov sahifasi  

- **Dars Sahifasi:**  
  - Video pleyer (Camtasia/CapCut videolar uchun)  
  - Materiallar yuklab olish tugmasi  
  - Dars ostida test bloklari  

- **Leaderboard Sahifasi:**  
  - Top 10 talik o‘quvchilar  
  - Sinflar bo‘yicha filter (7, 8, 9, 10, 11)  
  - Mavzular bo‘yicha natijalar filtri  

- **O‘qituvchi Paneli:**  
  - Grafiklar (Chart.js yoki Recharts yordamida) orqali o‘zlashtirish ko‘rsatkichlari  

---

## 5. Gamifikatsiya va Aqlli Mantiq

- **Progress Tracking:**  
  - O‘quvchi videoni ko‘rib bo‘lgach va testni yechgachgina keyingi mavzu ochilishi (Lock/Unlock tizimi)  

- **Smart Feedback:**  
  - Agar o‘quvchi testdan 50% dan kam ball olsa, tizim:  
    > "Ushbu mavzuni qayta o‘qib chiqishingizni maslahat beramiz"  
    degan notification chiqarishi kerak  

- **Badges:**  
  - "Bilimdon"  
  - "Tezkor"  
  - "Super O‘quvchi"  
  kabi virtual nishonlar  

---

## 6. Xavfsizlik va Ishlash unumdorligi

- **Video Streaming:**  
  - Videolarni xavfsiz host qilish (To‘g‘ridan-to‘g‘ri linkni osonlikcha ko‘chirib bo‘lmasligi)  

- **Caching:**  
  - Reyting jadvalini har safar DB dan so‘ramaslik uchun keshlashtirish  

- **JWT Auth:**  
  - Frontend va Backend o‘rtasida xavfsiz ma’lumot almashinuvi  