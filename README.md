# 📚 BookHive

BookHive — это полноценный онлайн-магазин книг, реализованный на Django с использованием Docker, Celery, Redis, PostgreSQL и REST API.

## 🚀 Основные функции

- 📖 Каталог книг с фильтрами и сортировкой
- 🔍 Поиск по названию и описанию
- 🛒 Корзина и оформление заказов
- 💰 Система скидок, промокодов и кэшбэка
- 🔔 Уведомления (WebSocket + email)
- ❤️ Избранное
- 🧾 История заказов и отзывов
- 👤 Личный кабинет с редактированием профиля
- 🛠️ Панель администратора
- 🔐 JWT-аутентификация
- 🧪 API-доступ к ключевым функциям
- 📊 Отчёты и аналитика (в процессе)

## 🧰 Стек технологий

- **Backend:** Django, Django REST Framework
- **Фоновая обработка:** Celery + Redis
- **База данных:** PostgreSQL
- **Контейнеризация:** Docker + Docker Compose
- **Асинхронность:** Django Channels + Redis
- **CI/CD:** GitHub Actions (опционально)
- **Email:** SMTP (Gmail)

## 🧪 Как запустить локально

```bash
# Клонировать репозиторий
git clone https://github.com/Alexander-Vialichko-790/Bookhive.git
cd Bookhive

# Сборка и запуск Docker-контейнеров
docker-compose up --build

# Создать суперпользователя
docker-compose exec web python manage.py createsuperuser
