# Скрипт для очистки базы данных (PowerShell)

Write-Host "Очистка базы данных..." -ForegroundColor Cyan
Write-Host ""

# Переходим в корневую директорию проекта
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

# Активируем виртуальное окружение если оно есть
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Запускаем скрипт очистки
python scripts\clear_database.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "База данных успешно очищена!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Ошибка при очистке базы данных!" -ForegroundColor Red
    exit 1
}

