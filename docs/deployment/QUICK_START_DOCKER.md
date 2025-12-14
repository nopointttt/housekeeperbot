# 🚀 Быстрый старт с Docker

## Шаг 1: Установка Docker

### Windows
Скачайте и установите [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Linux
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo usermod -aG docker $USER
newgrp docker
```

## Шаг 2: Настройка проекта

```bash
# Скопируйте пример файла окружения
cp .env.example .env

# Откройте .env и заполните:
# - BOT_TOKEN (получить у @BotFather)
# - WAREHOUSEMAN_ID (узнать у @userinfobot)
# - MANAGER_ID (узнать у @userinfobot)
```

## Шаг 3: Запуск

```bash
# Запустить все сервисы
docker compose up -d

# Посмотреть логи
docker compose logs -f bot
```

## Шаг 4: Проверка

Откройте Telegram, найдите вашего бота и отправьте `/start`

## Полезные команды

```bash
# Остановить
docker compose stop

# Перезапустить
docker compose restart

# Остановить и удалить
docker compose down

# Просмотр логов
docker compose logs -f bot
```

Подробная инструкция: см. `DOCKER_DEPLOY.md`

