# Деплой сайта на Cloudflare Pages

## GitHub репозиторий

**Репозиторий:** https://github.com/nopointttt/housekeeperbot.git  
**Ветка:** `main`  
**Подпапка с сайтом:** `website/`

## Настройка в Cloudflare Pages

### Шаг 1: Создание проекта

1. Перейди на [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Выбери **Pages** в боковом меню
3. Нажми **Create a project**
4. Выбери **Connect to Git**

### Шаг 2: Подключение репозитория

1. Авторизуйся через GitHub (если еще не авторизован)
2. Выбери репозиторий: **nopointttt/housekeeperbot**
3. Нажми **Begin setup**

### Шаг 3: Настройка билда

Заполни следующие поля:

- **Project name:** `housekeeper-landing` (или любое другое имя)
- **Production branch:** `main`
- **Framework preset:** `None` (или `Plain HTML`)
- **Build command:** (оставь пустым, так как это статический сайт)
- **Build output directory:** `website`

### Шаг 4: Деплой

1. Нажми **Save and Deploy**
2. Cloudflare автоматически задеплоит сайт
3. После завершения деплоя получишь URL типа: `housekeeper-landing.pages.dev`

## Структура сайта

```
website/
├── index.html                    # Главная страница
├── hotels.html                   # Страница для отелей
├── hostels.html                  # Страница для хостелов
├── management-companies.html     # Страница для УК
├── sanatoriums.html              # Страница для санаториев
├── styles.css                    # Стили
├── script.js                     # JavaScript
├── _headers                      # HTTP заголовки (безопасность)
├── _redirects                    # Редиректы (если нужны)
└── images/                       # Изображения
```

## Автоматический деплой

После настройки, каждое изменение в ветке `main` автоматически триггерит новый деплой на Cloudflare Pages.

## Кастомный домен

После деплоя можно подключить свой домен:

1. В настройках проекта Cloudflare Pages выбери **Custom domains**
2. Добавь свой домен (например, `housekeeper.ru` или `housekeeper.com`)
3. Следуй инструкциям по настройке DNS записей

## Проверка деплоя

После деплоя проверь:
- ✅ Главная страница открывается: `https://housekeeper-landing.pages.dev/`
- ✅ Все ссылки работают
- ✅ Стили и скрипты загружаются корректно
- ✅ Мобильная версия отображается правильно

## Полезные ссылки

- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [GitHub репозиторий](https://github.com/nopointttt/housekeeperbot)
- [Cloudflare Dashboard](https://dash.cloudflare.com/)

