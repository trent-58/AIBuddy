# AI Buddy — Backend ishga tushirish

## 1. Poetry o‘rnatilganligini tekshiring
```powershell
poetry --version
```
Agar yo‘q bo‘lsa: https://python-poetry.org/docs/ dan o‘rnating.

## 2. Backend papkasiga o‘ting
```powershell
cd "c:\Users\Hp\OneDrive\Desktop\Ai Buddy Hackaton\AIBuddy\backend"
```

## 3. Kutubxonalarni o‘rnating (Django va boshqalar)
```powershell
poetry install
```

## 4. Loyihani ishga tushiring
```powershell
poetry run python manage.py runserver
```

## Boshqa foydali buyruqlar
- Superuser yaratish: `poetry run python manage.py createsuperuser`
- Migrations: `poetry run python manage.py migrate`

**Eslatma:** `poetry` yozing, `poerty` emas.
