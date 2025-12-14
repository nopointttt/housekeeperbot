@echo off
REM Скрипт запуска тестов для Windows
REM Использование: scripts\run_tests.bat [опция]
REM Опции:
REM   all       - запустить все тесты (по умолчанию)
REM   unit      - только unit тесты
REM   int       - только интеграционные тесты
REM   e2e       - только e2e тесты
REM   cov       - с покрытием кода
REM   html      - с HTML отчетом покрытия

setlocal

REM Активируем виртуальное окружение если не активировано
if not defined VIRTUAL_ENV (
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
    )
)

set OPTION=%1
if "%OPTION%"=="" set OPTION=all

echo ========================================
echo  Запуск тестов: %OPTION%
echo ========================================
echo.

if "%OPTION%"=="all" (
    echo Запуск всех тестов...
    pytest tests\ -v
    goto :end
)

if "%OPTION%"=="unit" (
    echo Запуск unit тестов...
    pytest tests\unit\ -v
    goto :end
)

if "%OPTION%"=="int" (
    echo Запуск интеграционных тестов...
    pytest tests\integration\ -v
    goto :end
)

if "%OPTION%"=="e2e" (
    echo Запуск e2e тестов...
    pytest tests\e2e\ -v
    goto :end
)

if "%OPTION%"=="cov" (
    echo Запуск с покрытием...
    pytest tests\ --cov=bot --cov-report=term-missing -v
    goto :end
)

if "%OPTION%"=="html" (
    echo Запуск с HTML отчетом покрытия...
    pytest tests\ --cov=bot --cov-report=html --cov-report=term -v
    echo.
    echo HTML отчет сохранен в: htmlcov\index.html
    goto :end
)

echo Неизвестная опция: %OPTION%
echo Доступные опции: all, unit, int, e2e, cov, html

:end
echo.
echo ========================================
echo  Тесты завершены
echo ========================================

