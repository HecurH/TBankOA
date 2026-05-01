# TBankOA

Python-библиотека для асинхронной работы с [API Интернет-эквайринга](https://developer.tbank.ru/eacq/api) от ТБанка. Поддерживает инициализацию платежей, проверку статусов, отмену транзакций и обработку вебхуков.

Изначально не предполагалось выкладывать в общий доступ это нечто, возможно оно хоть частично и поможет кому-то.

## Возможности

- ✅ Асинхронный клиент для работы с API
- ✅ Поддержка всех основных операций:
  - Инициализация платежа
  - Получение статуса платежа
  - Получение статуса заказа
  - Отмена платежа (полная и частичная)
- ✅ Обработка вебхуков с проверкой подписи
- ✅ Типизированные модели запросов и ответов
- ✅ Генерация и верификация подписей SHA-256

## Установка

```bash
pip install git+https://github.com/HecurH/TBankOA.git
```

## Быстрый старт

### Инициализация клиента

```python
from TBankOA import AsyncOnlineAcquiringClient

client = AsyncOnlineAcquiringClient(
    terminal_key="YOUR_TERMINAL_KEY",
    password="YOUR_PASSWORD"
)
```

### Инициализация платежа

```python
response = await client.initialize_payment(
    amount=10000,  # сумма в копейках
    order_id="unique_order_123",
    description="Оплата заказа #123"
)

print(response.PaymentURL)  # URL для перенаправления на форму оплаты
```

### Проверка статуса платежа

```python
state = await client.get_payment_state(payment_id="123456")
print(state.Status)  # PaymentStatus enum
```

### Отмена платежа

```python
# Полная отмена
await client.cancel_payment(payment_id="123456")

# Частичная отмена
await client.cancel_payment(
    payment_id="123456",
    amount=5000  # сумма в копейках
)
```

## Обработка вебхуков

```python
from TBankOA import WebhookProcessor, PaymentStatus

processor = WebhookProcessor(password="YOUR_PASSWORD")

# Обработка конкретных статусов
@processor.on(PaymentStatus.CONFIRMED, PaymentStatus.CANCELED)
async def handle_payment(payload):
    print(f"Payment {payload.PaymentId} changed to {payload.Status}")
    # ...

# Обработка всех статусов
@processor.on_any
async def log_all(payload):
    print(f"Webhook received: {payload.Status}")

# Обработка входящего запроса
result = await processor.handle(request_data)  # "OK" или "FAIL"
```


## Лицензия

MIT
