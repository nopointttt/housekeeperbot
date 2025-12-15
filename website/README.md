# Housekeeper Landing Page

Landing page для продукта Housekeeper - автоматизация управления заявками и складом для отелей и управляющих компаний.

## Структура

- `index.html` - главная страница
- `styles.css` - стили
- `script.js` - JavaScript для интерактивности
- `README.md` - этот файл

## Деплой на Cloudflare Pages

### Способ 1: Через GitHub

1. Создайте репозиторий на GitHub (или используйте существующий)
2. Добавьте папку `website/` в репозиторий
3. Перейдите на [Cloudflare Dashboard](https://dash.cloudflare.com/)
4. Выберите **Pages** → **Create a project** → **Connect to Git**
5. Выберите ваш GitHub репозиторий
6. Настройте проект:
   - **Project name**: `housekeeper-landing` (или любое другое)
   - **Production branch**: `main` (или `master`)
   - **Build command**: (оставьте пустым, так как это статический сайт)
   - **Build output directory**: `website`
7. Нажмите **Save and Deploy**
8. Cloudflare автоматически задеплоит сайт и даст вам URL типа `housekeeper-landing.pages.dev`

### Способ 2: Через Wrangler CLI

1. Установите Wrangler:
   ```bash
   npm install -g wrangler
   ```

2. Войдите в Cloudflare:
   ```bash
   wrangler login
   ```

3. Перейдите в папку `website/`:
   ```bash
   cd website
   ```

4. Задеплойте:
   ```bash
   wrangler pages deploy .
   ```

### Способ 3: Через drag & drop в Cloudflare Dashboard

1. Создайте ZIP-архив содержимого папки `website/`
2. Перейдите на [Cloudflare Dashboard](https://dash.cloudflare.com/)
3. Выберите **Pages** → **Create a project** → **Upload assets**
4. Перетащите ZIP-архив в окно загрузки
5. Нажмите **Deploy site**

## Кастомизация домена

После деплоя вы можете подключить свой домен:

1. В настройках проекта на Cloudflare Pages выберите **Custom domains**
2. Добавьте свой домен (например, `housekeeper.ru` или `housekeeper.com`)
3. Следуйте инструкциям по настройке DNS

## Обновление контента

После изменения файлов в папке `website/`:

- Если используете GitHub: просто сделайте `git push`, Cloudflare автоматически передеплоит
- Если используете Wrangler: выполните `wrangler pages deploy .` заново
- Если используете drag & drop: загрузите новый ZIP-архив

## Контакты на сайте

Текущие контакты:
- **Telegram**: @barefootdao
- **Телефон/WhatsApp**: +7 (980) 458-48-76

Для изменения контактов отредактируйте секцию `#contact` в `index.html`.

## Тестирование локально

Для локального просмотра сайта просто откройте `index.html` в браузере или используйте простой HTTP-сервер:

```bash
# Python 3
python -m http.server 8000

# Node.js (npx)
npx serve

# PHP
php -S localhost:8000
```

Затем откройте `http://localhost:8000` в браузере.
