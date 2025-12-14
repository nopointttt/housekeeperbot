"""Fixtures для тестовых данных"""
import pytest
from datetime import datetime, timedelta
from faker import Faker
from bot.database.models import User, Request, RequestPhoto, WarehouseItem, Complaint

# Русский Faker для генерации тестовых данных
fake = Faker('ru_RU')


@pytest.fixture
def test_user_data() -> dict:
    """Данные для создания тестового пользователя"""
    return {
        "id": fake.random_int(min=100000, max=999999),
        "role": "employee"
    }


@pytest.fixture
def test_employee_data() -> dict:
    """Данные для сотрудника"""
    return {
        "id": 100001,
        "role": "employee"
    }


@pytest.fixture
def test_warehouseman_data() -> dict:
    """Данные для завхоза"""
    return {
        "id": 999001,
        "role": "warehouseman"
    }


@pytest.fixture
def test_manager_data() -> dict:
    """Данные для руководителя"""
    return {
        "id": 999002,
        "role": "manager"
    }


@pytest.fixture
async def test_user(test_session, test_employee_data) -> User:
    """Создать тестового пользователя (сотрудника) в БД"""
    user = User(**test_employee_data)
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def test_warehouseman(test_session, test_warehouseman_data) -> User:
    """Создать завхоза в БД"""
    user = User(**test_warehouseman_data)
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
async def test_manager(test_session, test_manager_data) -> User:
    """Создать руководителя в БД"""
    user = User(**test_manager_data)
    test_session.add(user)
    await test_session.flush()
    return user


@pytest.fixture
def test_request_data(test_employee_data) -> dict:
    """Данные для создания тестовой заявки"""
    return {
        "number": f"ЗХ-{datetime.now().strftime('%d%m%y')}-001",
        "user_id": test_employee_data["id"],
        "category": "Канцелярия",
        "description": fake.sentence(nb_words=5),
        "quantity": fake.random_int(min=1, max=100),
        "priority": fake.random_element(["normal", "urgent"]),
        "status": "new"
    }


@pytest.fixture
async def test_request(test_session, test_user, test_request_data) -> Request:
    """Создать тестовую заявку в БД"""
    request = Request(**test_request_data)
    test_session.add(request)
    await test_session.flush()
    return request


@pytest.fixture
async def test_request_with_photos(test_session, test_user) -> Request:
    """Создать заявку с фотографиями"""
    request = Request(
        number=f"ЗХ-{datetime.now().strftime('%d%m%y')}-002",
        user_id=test_user.id,
        category="Хозтовары и уборка",
        description="Заявка с фото для тестирования",
        quantity=5,
        priority="urgent",
        status="new"
    )
    test_session.add(request)
    await test_session.flush()
    
    # Добавляем фото
    for i in range(3):
        photo = RequestPhoto(
            request_id=request.id,
            file_id=f"test_file_id_{i}"
        )
        test_session.add(photo)
    
    await test_session.flush()
    return request


@pytest.fixture
def test_warehouse_item_data() -> dict:
    """Данные для позиции на складе"""
    return {
        "name": fake.word().capitalize() + " " + fake.word(),
        "current_quantity": fake.random_int(min=0, max=100),
        "min_quantity": fake.random_int(min=5, max=20)
    }


@pytest.fixture
async def test_warehouse_item(test_session, test_warehouse_item_data) -> WarehouseItem:
    """Создать позицию на складе в БД"""
    item = WarehouseItem(**test_warehouse_item_data)
    test_session.add(item)
    await test_session.flush()
    return item


@pytest.fixture
async def test_warehouse_items(test_session) -> list[WarehouseItem]:
    """Создать несколько позиций на складе"""
    items = []
    names = ["Бумага А4", "Ручки синие", "Карандаши", "Скрепки", "Степлеры"]
    
    for i, name in enumerate(names):
        item = WarehouseItem(
            name=name,
            current_quantity=fake.random_int(min=0, max=50),
            min_quantity=10
        )
        test_session.add(item)
        items.append(item)
    
    await test_session.flush()
    return items


@pytest.fixture
async def test_low_stock_items(test_session) -> list[WarehouseItem]:
    """Создать позиции с низким остатком (<= минимума)"""
    items = []
    
    # Позиция с остатком = минимуму
    item1 = WarehouseItem(name="Товар на минимуме", current_quantity=10, min_quantity=10)
    test_session.add(item1)
    items.append(item1)
    
    # Позиция с остатком < минимума
    item2 = WarehouseItem(name="Товар ниже минимума", current_quantity=5, min_quantity=15)
    test_session.add(item2)
    items.append(item2)
    
    # Позиция с нулевым остатком
    item3 = WarehouseItem(name="Товар закончился", current_quantity=0, min_quantity=5)
    test_session.add(item3)
    items.append(item3)
    
    await test_session.flush()
    return items


@pytest.fixture
def test_complaint_data(test_employee_data) -> dict:
    """Данные для жалобы"""
    return {
        "user_id": test_employee_data["id"],
        "reason": "Долгое выполнение",
        "text": fake.paragraph(nb_sentences=2)
    }


@pytest.fixture
async def test_complaint(test_session, test_user, test_request, test_complaint_data) -> Complaint:
    """Создать тестовую жалобу в БД"""
    complaint = Complaint(
        request_id=test_request.id,
        **test_complaint_data
    )
    test_session.add(complaint)
    await test_session.flush()
    return complaint


# ===== Генераторы данных =====

def generate_random_user_id() -> int:
    """Сгенерировать случайный Telegram ID"""
    return fake.random_int(min=100000, max=999999999)


def generate_request_number(date: datetime = None) -> str:
    """Сгенерировать номер заявки"""
    if date is None:
        date = datetime.now()
    sequence = fake.random_int(min=1, max=999)
    return f"ЗХ-{date.strftime('%d%m%y')}-{sequence:03d}"


def generate_category() -> str:
    """Сгенерировать категорию заявки"""
    categories = [
        "Канцелярия",
        "Чай, кофе, сахар, вода",
        "Хозтовары и уборка",
        "ИТ-оборудование и расходники",
        "Ремонт мебели",
        "Ремонт сантехники",
        "Ремонт электрики",
        "Другое"
    ]
    return fake.random_element(categories)


def generate_priority() -> str:
    """Сгенерировать приоритет"""
    return fake.random_element(["normal", "urgent"])


def generate_status() -> str:
    """Сгенерировать статус заявки"""
    return fake.random_element(["new", "in_progress", "completed", "rejected"])

