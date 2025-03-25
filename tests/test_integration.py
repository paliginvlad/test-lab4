import uuid

import boto3
from app.eshop import Product, ShoppingCart, Order
import random
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from datetime import datetime, timedelta, timezone
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE
import pytest


@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (8662354, 123456),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)

    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id, "Actual shipping id must be equal to mock return value"

    mock_repo.create_shipping.assert_called_with(ShippingService.list_available_shipping_type()[0], ["Product"], order_id, shipping_service.SHIPPING_CREATED, due_date)
    mock_publisher.send_new_shipping.assert_called_with(shipping_id)


def test_place_order_with_unavailable_shipping_type_fails(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )
    order = Order(cart, shipping_service)
    shipping_id = None

    with pytest.raises(ValueError) as excinfo:
        shipping_id = order.place_order(
            "Новий тип доставки",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=3)
        )
    assert shipping_id is None, "Shipping id must not be assigned"
    assert "Shipping type is not available" in str(excinfo.value)



def test_when_place_order_then_shipping_in_queue(dynamo_resource):
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()

    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    assert len(messages) == 1, "Expected 1 SQS message"

    body = messages[0]["Body"]
    assert shipping_id == body



# Тест 1: Перевірка створення запису в ShippingRepository
def test_shipping_repository_create_shipping(dynamo_resource):
    repo = ShippingRepository()
    shipping_id = repo.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["product1", "product2"],
        order_id=str(uuid.uuid4()),
        status="created",
        due_date=datetime.now(timezone.utc) + timedelta(seconds=5)
    )
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_id"] == shipping_id
    assert shipping["shipping_type"] == "Нова Пошта"
    assert shipping["product_ids"] == "product1,product2"
    assert shipping["shipping_status"] == "created"

# Тест 2: Перевірка оновлення статусу в ShippingRepository
def test_shipping_repository_update_status(dynamo_resource):
    repo = ShippingRepository()
    shipping_id = repo.create_shipping(
        shipping_type="Укр Пошта",
        product_ids=["product1"],
        order_id=str(uuid.uuid4()),
        status="created",
        due_date=datetime.now(timezone.utc) + timedelta(seconds=5)
    )
    repo.update_shipping_status(shipping_id, "in progress")
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_status"] == "in progress"

# Тест 3: Перевірка відправки повідомлення в SQS через ShippingPublisher
def test_shipping_publisher_send_message(dynamo_resource):
    publisher = ShippingPublisher()
    shipping_id = str(uuid.uuid4())
    message_id = publisher.send_new_shipping(shipping_id)
    assert message_id is not None
    messages = publisher.poll_shipping()
    assert shipping_id in messages

# Тест 4: Перевірка отримання повідомлень із черги через ShippingPublisher
def test_shipping_publisher_poll_messages(dynamo_resource):
    publisher = ShippingPublisher()
    shipping_id1 = str(uuid.uuid4())
    shipping_id2 = str(uuid.uuid4())
    publisher.send_new_shipping(shipping_id1)
    publisher.send_new_shipping(shipping_id2)
    messages = publisher.poll_shipping(batch_size=2)
    assert len(messages) == 2
    assert shipping_id1 in messages
    assert shipping_id2 in messages

# Тест 5: Перевірка створення доставки через ShippingService
def test_shipping_service_create_shipping(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    shipping_id = service.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["product1"],
        order_id=str(uuid.uuid4()),
        due_date=datetime.now(timezone.utc) + timedelta(seconds=5)
    )
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_status"] == "in progress"
    messages = publisher.poll_shipping()
    assert shipping_id in messages

# Тест 6: Перевірка завершення доставки через ShippingService
def test_shipping_service_complete_shipping(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    shipping_id = repo.create_shipping(
        shipping_type="Самовивіз",
        product_ids=["product1"],
        order_id=str(uuid.uuid4()),
        status="in progress",
        due_date=datetime.now(timezone.utc) + timedelta(seconds=5)
    )
    service.complete_shipping(shipping_id)
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_status"] == "completed"

# Тест 7: Перевірка провалу доставки через ShippingService, якщо прострочено
def test_shipping_service_fail_shipping_if_overdue(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    shipping_id = repo.create_shipping(
        shipping_type="Meest Express",
        product_ids=["product1"],
        order_id=str(uuid.uuid4()),
        status="in progress",
        due_date=datetime.now(timezone.utc) - timedelta(seconds=5)  # Прострочено
    )
    service.process_shipping(shipping_id)
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_status"] == "failed"

# Тест 8: Перевірка інтеграції ShoppingCart із Order та ShippingService
def test_order_place_with_valid_cart(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    cart = ShoppingCart()
    product = Product(name="Test Product", price=100.0, available_amount=10)
    cart.add_product(product, 5)
    order = Order(cart, service)
    shipping_id = order.place_order("Нова Пошта", datetime.now(timezone.utc) + timedelta(seconds=5))
    shipping = repo.get_shipping(shipping_id)
    assert shipping["shipping_status"] == "in progress"
    assert product.available_amount == 5  # Перевірка списання товару

# Тест 9: Перевірка обробки батчу доставок через ShippingService
def test_shipping_service_process_batch(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    shipping_id1 = service.create_shipping(
        shipping_type="Нова Пошта",
        product_ids=["product1"],
        order_id=str(uuid.uuid4()),
        due_date=datetime.now(timezone.utc) + timedelta(seconds=5)
    )
    # Створюємо доставку з датою в минулому через repository напряму, щоб обійти обмеження create_shipping
    shipping_id2 = repo.create_shipping(
        shipping_type="Укр Пошта",
        product_ids=["product2"],
        order_id=str(uuid.uuid4()),
        status="in progress",
        due_date=datetime.now(timezone.utc) - timedelta(seconds=5)  # Прострочено
    )
    publisher.send_new_shipping(shipping_id2)  # Додаємо в чергу вручну
    service.process_shipping_batch()
    shipping1 = repo.get_shipping(shipping_id1)
    shipping2 = repo.get_shipping(shipping_id2)
    assert shipping1["shipping_status"] == "completed"
    assert shipping2["shipping_status"] == "failed"

# Тест 10: Перевірка повного циклу Order із невалідним типом доставки
def test_order_place_with_invalid_shipping_type_fails(dynamo_resource):
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)
    cart = ShoppingCart()
    product = Product(name="Test Product", price=100.0, available_amount=10)
    cart.add_product(product, 5)
    order = Order(cart, service)
    with pytest.raises(ValueError) as excinfo:
        order.place_order("Invalid Shipping", datetime.now(timezone.utc) + timedelta(seconds=5))
    assert "Shipping type is not available" in str(excinfo.value)
    assert product.available_amount == 5
    assert not cart.products
