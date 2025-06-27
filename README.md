# Foodgram

Платформа для публикации и обмена кулинарными рецептами. Пользователи могут публиковать собственные блюда, подписываться на любимых авторов, добавлять рецепты в избранное и формировать список покупок одним кликом.

---

## Возможности

| Функция                   | Описание                                                                 |
| ------------------------- | ------------------------------------------------------------------------ |
| Регистрация / авторизация | Djoser + JWT / Token, смена пароля, восстановление                       |
| Публикация рецептов       | фото, ингредиенты (кол‑во и единицы), теги, время приготовления          |
| Избранное                 | быстрый доступ к любимым рецептам                                        |
| Подписки                  | лента публикаций интересных авторов                                      |
| Список покупок            | агрегирование ингредиентов из нескольких рецептов → TXT‑файл             |
| Поиск и фильтры           | поиск ингредиентов с автодополнением, фильтр по тегам/авторам/избранному |
| Админ‑панель              | удобное редактирование моделей и статистика по рецептам                  |

---

## Технологический стек

- Backend: Python 3.9, Django 4.2, Django REST Framework, Djoser, JWT, PostgreSQL
- Frontend: React 18 SPA (каталог `frontend`, сборка внутри Docker)
- DevOps: Docker Compose, Nginx 1.25, Gunicorn 21, CI/CD на GitHub Actions, Docker Hub
- Библиотеки: django‑filters, Pillow, psycopg2‑binary, python‑decouple, Simple JWT, social‑auth

---

## Разворачивание проекта (Docker)

### 1. Клонирование репозитория

```bash
git clone
cd foodgram/infra            # каталог с docker‑compose.yml
```

### 2. Создание файла `.env`

```dotenv
# База данных
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_pass
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=your_super_secret_key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,<your_domain>
```

### 3. Сборка и запуск контейнеров

```bash
docker compose up -d --build
```

Контейнеры и порты:

| Сервис   | Порт | Назначение                       |
| -------- | ---- | -------------------------------- |
| db       | 5432 | PostgreSQL 13                    |
| backend  | 8000 | Gunicorn → Django WSGI           |
| frontend | —    | Сборка React, результат → volume |
| nginx    | 80   | Статика, медиa, прокси `/api`    |

### 4. Миграции и загрузка ингредиентов автоматические через entrypoint

Доступы:

- [http://localhost/](http://localhost/) — клиентское SPA
- [http://localhost/admin/](http://localhost/admin/) — админ‑панель Django
- [http://localhost/api/docs/](http://localhost/api/docs/) — swagger‑документация

---

## Локальная разработка без Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r backend/src/requirements.txt
cp backend/src/.env.example backend/src/.env
cd backend/src
python manage.py migrate
python manage.py runserver
```

## Структура репозитория

```
.
├── backend/         # исходники Django‑проекта
│   └── src/
│       ├── foodgram/    # settings, wsgi, urls
│       ├── api/         # viewsets, serializers, filters
│       ├── recipes/     # модели рецептов
│       └── users/       # кастомная модель пользователя
│
├── frontend/        # React‑приложение
├── infra/           # docker‑compose, nginx.conf
├── data/            # фикстуры (ингредиенты) CSV/JSON
└── docs/            # OpenAPI‑спека, swagger
```

---

## Документация API

- Swagger / Redoc: `/api/docs/`
- JSON OpenAPI‑спека: `docs/openapi.json`
- Токен‑авторизация: `POST /api/auth/token/login/` → `Authorization: Token <token>`

Основные эндпоинты:

| Группа       | Endpoint                                  | Описание                 |
| ------------ | ----------------------------------------- | ------------------------ |
| Авторизация  | /auth/token/…                             | Djoser / Token / JWT     |
| Пользователи | /users/                                   | список, подписки, аватар |
| Рецепты      | /recipes/                                 | CRUD рецептов            |
| Теги         | /tags/                                    | список тегов             |
| Ингредиенты  | /ingredients/                             | поиск с автодополнением  |
| Списки       | /recipes/{id}/favorite/ и /shopping_cart/ | избранное, покупки       |

---

## Автор

| Имя                     | Контакты               |
| ----------------------- | ---------------------- |
| **Романова Александра** | Telegram: @pogromanova |

---

## Лицензия

Проект распространяется под лицензией MIT © <YEAR> <YOUR NAME>
