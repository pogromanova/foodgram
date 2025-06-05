# 🍲 Продуктовый помощник "Foodgram"

*Последнее обновление: 2025-06-05 19:20:24*  
*Автор документации: pogromanova

## 📋 О проекте

"Продуктовый помощник" (Foodgram) — это современный веб-сервис для публикации и обмена кулинарными рецептами. Платформа предоставляет удобный интерфейс для создания, поиска и хранения рецептов, а также для формирования списка покупок на основе выбранных блюд.

## 💻 Технический стек

### Бэкенд
- ![Python](https://img.shields.io/badge/Python-3.7+-blue)
- ![Django](https://img.shields.io/badge/Django-3.2+-green)
- ![DRF](https://img.shields.io/badge/DRF-latest-red)
- ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-latest-blue)

### Фронтенд
- ![React](https://img.shields.io/badge/React-latest-blue)

### Развертывание
- ![Docker](https://img.shields.io/badge/Docker-latest-blue)
- ![Docker Compose](https://img.shields.io/badge/Docker_Compose-latest-blue)
- ![Nginx](https://img.shields.io/badge/Nginx-1.21+-green)
- ![Gunicorn](https://img.shields.io/badge/Gunicorn-latest-green)

## 🏗️ Архитектура проекта

Приложение развертывается с использованием Docker и состоит из четырех основных компонентов:

| Контейнер | Сервис | Описание |
|-----------|--------|----------|
| `postgres` | База данных | PostgreSQL для хранения данных |
| `api` | Бэкенд | Django REST API сервер |
| `web-client` | Фронтенд | React приложение (используется для сборки) |
| `web-server` | Веб-сервер | Nginx для обслуживания статики и проксирования запросов |

## 🚀 Руководство по развертыванию

### Предварительные требования

- Установленный Docker и Docker Compose
- Git для клонирования репозитория

### Установка и запуск

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/username/foodgram-project-react.git
   cd foodgram-project-react
   ```

2. **Настройка переменных окружения**
   
   Создайте файл `.env` в директории `/infra/` со следующими параметрами:

   ```dotenv
   # PostgreSQL конфигурация
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   DB_HOST=postgres
   DB_PORT=5432
   
   # Django конфигурация
   SECRET_KEY=your-secure-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
   
   # Путь к файлу с ингредиентами
   INGREDIENTS_FILE_PATH=/app/data/ingredients.json
   ```

3. **Запуск контейнеров**
   ```bash
   cd infra
   docker-compose up -d
   ```

4. **Проверка работоспособности**
   
   После успешного запуска:
   - Основной сайт: http://localhost/
   - API документация: http://localhost/api/docs/

## 🔍 Возможности платформы

### Для всех посетителей
- Просмотр главной страницы с каталогом рецептов
- Детальный просмотр отдельных рецептов
- Просмотр профилей пользователей
- Регистрация и авторизация

### Для зарегистрированных пользователей
- Публикация собственных рецептов
- Редактирование и удаление своих рецептов
- Добавление рецептов в "Избранное"
- Подписка на интересных авторов
- Формирование списка покупок на основе рецептов
- Экспорт списка необходимых ингредиентов в TXT-формате
- Управление профилем и учетными данными

### Для администраторов
- Полный доступ к административной панели
- Управление всеми рецептами на платформе
- Модерация контента и пользователей
- Управление справочниками ингредиентов и тегов

## 📡 REST API

API платформы документировано с использованием ReDoc и доступно по адресу `/api/docs/` после запуска проекта.

### Основные эндпоинты

| Ресурс | Описание | Методы |
|--------|----------|--------|
| `/api/users/` | Работа с пользователями | GET, POST |
| `/api/tags/` | Получение тегов рецептов | GET |
| `/api/ingredients/` | Получение и поиск ингредиентов | GET |
| `/api/recipes/` | Работа с рецептами | GET, POST, PATCH, DELETE |
| `/api/recipes/download_shopping_cart/` | Скачивание списка покупок | GET |

## 👨‍💻 Контактная информация

**Разработчик**: Александра  
**Email**: 89067785950ar@gmail.com

---

© 2025 Foodgram - "Продуктовый помощник". Все права защищены.# diploma1
