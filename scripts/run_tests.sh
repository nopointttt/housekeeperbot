#!/bin/bash
# Скрипт запуска тестов для Linux/Mac
# Использование: ./scripts/run_tests.sh [опция]
# Опции:
#   all       - запустить все тесты (по умолчанию)
#   unit      - только unit тесты
#   int       - только интеграционные тесты
#   e2e       - только e2e тесты
#   cov       - с покрытием кода
#   html      - с HTML отчетом покрытия

# Активируем виртуальное окружение если не активировано
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
fi

OPTION=${1:-all}

echo "========================================"
echo " Запуск тестов: $OPTION"
echo "========================================"
echo

case $OPTION in
    all)
        echo "Запуск всех тестов..."
        pytest tests/ -v
        ;;
    unit)
        echo "Запуск unit тестов..."
        pytest tests/unit/ -v
        ;;
    int)
        echo "Запуск интеграционных тестов..."
        pytest tests/integration/ -v
        ;;
    e2e)
        echo "Запуск e2e тестов..."
        pytest tests/e2e/ -v
        ;;
    cov)
        echo "Запуск с покрытием..."
        pytest tests/ --cov=bot --cov-report=term-missing -v
        ;;
    html)
        echo "Запуск с HTML отчетом покрытия..."
        pytest tests/ --cov=bot --cov-report=html --cov-report=term -v
        echo
        echo "HTML отчет сохранен в: htmlcov/index.html"
        ;;
    *)
        echo "Неизвестная опция: $OPTION"
        echo "Доступные опции: all, unit, int, e2e, cov, html"
        exit 1
        ;;
esac

echo
echo "========================================"
echo " Тесты завершены"
echo "========================================"

