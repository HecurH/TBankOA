"""
Тесты для TBankOA — запускать: pytest test_tbank.py -v
Зависимости: pip install pytest pytest-asyncio

Используется публичный тест-терминал T-Bank:
  TerminalKey = "TinkoffBankTest"
  Password    = "TinkoffBankTest"
"""

import hashlib
import uuid
import pytest
import pytest_asyncio

# ─── Настройки тест-терминала ────────────────────────────────────────────────

TERMINAL_KEY = "1234567890123DEMO"
PASSWORD      = "passpasspasspass"

# ─── Импорт вашей библиотеки ─────────────────────────────────────────────────

from TBankOA.clients import AsyncOnlineAcquiringClient
from TBankOA.schemas import WebhookPayload
from TBankOA.exceptions import TBankOAAPIError
from TBankOA.types.enums import PaymentStatus

# ─── Фикстуры ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    c = AsyncOnlineAcquiringClient(
        terminal_key=TERMINAL_KEY,
        password=PASSWORD,
    )
    yield c
    await c.close()


def unique_order() -> str:
    """Уникальный order_id для каждого теста (T-Bank требует уникальность)."""
    return str(uuid.uuid4())[:32]


# ═════════════════════════════════════════════════════════════════════════════
# 1. ИНИЦИАЛИЗАЦИЯ ПЛАТЕЖА
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_init_payment_returns_payment_url(client):
    """
    /Init должен вернуть PaymentURL (флоу платёжной формы банка).
    """
    resp = await client.initialize_payment(
        amount=100,           # 1 руб. в копейках
        order_id=unique_order(),
        description="Test payment",
    )

    assert resp.Success, f"Init failed: {resp.ErrorCode} — {resp.Message}"
    assert resp.PaymentId, "PaymentId не вернулся"
    assert resp.PaymentURL and resp.PaymentURL.startswith("https://"), (
        f"PaymentURL некорректен: {resp.PaymentURL}"
    )
    assert resp.Status == PaymentStatus.NEW, (
        f"Ожидался статус NEW, получен {resp.Status}"
    )

    print(f"\n✅ PaymentId: {resp.PaymentId}")
    print(f"   PaymentURL: {resp.PaymentURL}")


@pytest.mark.asyncio
async def test_init_payment_amount_in_kopecks(client):
    """
    Проверяем, что сумма возвращается в копейках без изменений.
    """
    amount = 5999  # 59 руб. 99 коп.
    resp = await client.initialize_payment(
        amount=amount,
        order_id=unique_order(),
        description="Amount check",
    )
    assert resp.Success
    assert resp.Amount == amount, (
        f"Ожидалась сумма {amount}, получено {resp.Amount}"
    )


@pytest.mark.asyncio
async def test_init_duplicate_order_id_raises(client):
    """
    Повторный вызов с тем же order_id должен вернуть ошибку.
    """
    order_id = unique_order()

    await client.initialize_payment(
        amount=100,
        order_id=order_id,
        description="First",
    )

    with pytest.raises(TBankOAAPIError):
        await client.initialize_payment(
            amount=200,
            order_id=order_id,
            description="Duplicate",
        )


# ═════════════════════════════════════════════════════════════════════════════
# 2. СТАТУС ПЛАТЕЖА
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_payment_state(client):
    """
    /GetState должен вернуть корректный статус для только что созданного платежа.
    """
    init = await client.initialize_payment(
        amount=100,
        order_id=unique_order(),
        description="State check",
    )

    state = await client.get_payment_state(init.PaymentId)

    assert state.Success
    assert state.PaymentId == init.PaymentId
    assert state.Status in (PaymentStatus.NEW, PaymentStatus.FORM_SHOWED), (
        f"Неожиданный статус: {state.Status}"
    )


@pytest.mark.asyncio
async def test_get_payment_state_invalid_id(client):
    """
    Несуществующий PaymentId должен бросать TBankOAAPIError.
    """
    with pytest.raises(TBankOAAPIError):
        await client.get_payment_state("000000000000")


# ═════════════════════════════════════════════════════════════════════════════
# 3. СТАТУС ЗАКАЗА
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_get_order_state(client):
    """
    /CheckOrder должен вернуть список платежей по order_id.
    """
    order_id = unique_order()
    init = await client.initialize_payment(
        amount=100,
        order_id=order_id,
        description="Order state check",
    )

    order = await client.get_order_state(order_id)

    assert order.Success
    assert order.OrderId == order_id
    assert order.Payments, "Список платежей пустой"

    payment_ids = [p.PaymentId for p in order.Payments if p]
    assert init.PaymentId in payment_ids, (
        f"PaymentId {init.PaymentId} не найден в заказе: {payment_ids}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# 4. ОТМЕНА ПЛАТЕЖА
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_cancel_payment(client):
    """
    /Cancel на платёж в статусе NEW должен успешно отменить его.
    """
    init = await client.initialize_payment(
        amount=500,
        order_id=unique_order(),
        description="Cancel test",
    )

    cancel = await client.cancel_payment(init.PaymentId)

    assert cancel.Success, f"Cancel failed: {cancel.ErrorCode} — {cancel.Message}"
    assert cancel.PaymentId == init.PaymentId
    # После отмены NEW → CANCELED
    assert cancel.Status == PaymentStatus.CANCELED, (
        f"Ожидался CANCELED, получен {cancel.Status}"
    )


@pytest.mark.asyncio
async def test_cancel_payment_partial_amount(client):
    """
    Частичная отмена: передаём Amount меньше оригинала.
    Для статуса NEW amount игнорируется, отмена всё равно на полную сумму.
    """
    init = await client.initialize_payment(
        amount=1000,
        order_id=unique_order(),
        description="Partial cancel test",
    )

    cancel = await client.cancel_payment(init.PaymentId, amount=300)

    assert cancel.Success
    # Для NEW — полная отмена несмотря на переданный Amount
    assert cancel.Status == PaymentStatus.CANCELED


# ═════════════════════════════════════════════════════════════════════════════
# 5. ВЕБХУК — верификация токена
# ═════════════════════════════════════════════════════════════════════════════

def _make_webhook_token(params: dict, password: str) -> str:
    """Эталонная генерация токена по алгоритму T-Bank (SHA-256)."""
    items = []

    def flatten(d):
        for k, v in d.items():
            if isinstance(v, (list, tuple, dict)):
                continue
            items.append((k, v))
            
    flatten(params)
    items.append(("Password", password))
    
    items.sort(key=lambda x: str(x[0]).lower())

    res = "".join(str(value) for _, value in items)

    return hashlib.sha256(res.encode()).hexdigest()

def _build_raw_webhook(overrides: dict | None = None) -> dict:
    base = {
        "TerminalKey": TERMINAL_KEY,
        "OrderId":    "test-order-001",
        "Success":    True,
        "Status":     "AUTHORIZED",
        "PaymentId":  "123456789",
        "ErrorCode":  "0",
        "Amount":     1000,
        "Pan":        "430000******0777",
        "ExpDate":    "1122",
    }
    if overrides:
        base.update(overrides)
    base["Token"] = _make_webhook_token(base, PASSWORD)
    
    return base


@pytest.mark.asyncio
async def test_webhook_valid_signature():
    """
    Вебхук с правильной подписью должен верифицироваться.
    """
    from TBankOA.schemas import WebhookPayload

    raw = _build_raw_webhook()
    payload = WebhookPayload(**raw)

    assert payload.verify_signature(PASSWORD), (
        "Верификация подписи провалилась для валидного вебхука"
    )


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    """
    Изменение любого поля должно сломать подпись.
    """
    raw = _build_raw_webhook()
    raw["Amount"] = 9999  # подделываем сумму, токен не пересчитываем

    payload = WebhookPayload(**raw)
    assert not payload.verify_signature(PASSWORD), (
        "Подпись прошла проверку на подделанном вебхуке — это ошибка"
    )


@pytest.mark.asyncio
async def test_webhook_with_data_field_ignored_in_signature():
    """
    Поле Data (вложенный объект) НЕ должно влиять на токен.
    Если Data добавлен после подписания — токен должен оставаться валидным.
    """
    raw = _build_raw_webhook()  # токен посчитан без Data

    # Добавляем Data ПОСЛЕ подписания (как это делает T-Bank для рассрочки)
    raw["Data"] = [{"Key": "Source", "Value": "Installment"}]

    payload = WebhookPayload(**raw)
    assert payload.verify_signature(PASSWORD), (
        "Токен сломался из-за поля Data — verify_signature должна его исключать"
    )


# ═════════════════════════════════════════════════════════════════════════════
# 6. WebhookProcessor
# ═════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_webhook_processor_dispatches_correct_handler():
    """
    WebhookProcessor должен вызвать хендлер для нужного статуса.
    """
    from TBankOA.clients import WebhookProcessor

    processor = WebhookProcessor(password=PASSWORD)
    received: list[WebhookPayload] = []

    @processor.on(PaymentStatus.AUTHORIZED)
    async def on_authorized(payload: WebhookPayload):
        received.append(payload)

    raw = _build_raw_webhook({"Status": "AUTHORIZED"})
    result = await processor.handle(raw)

    assert result == "OK"
    assert len(received) == 1
    assert received[0].PaymentId == "123456789"


@pytest.mark.asyncio
async def test_webhook_processor_returns_fail_on_bad_signature():
    """
    Вебхук с неверной подписью → processor.handle() возвращает FAIL.
    """
    from TBankOA.clients import WebhookProcessor

    processor = WebhookProcessor(password=PASSWORD)

    raw = _build_raw_webhook()
    raw["Token"] = "0000000000000000000000000000000000000000000000000000000000000000"

    result = await processor.handle(raw)
    assert result == "FAIL", f"Ожидался FAIL, получено '{result}'"


@pytest.mark.asyncio
async def test_webhook_processor_on_any_handler():
    """
    on_any должен вызываться для любого статуса.
    """
    from TBankOA.clients import WebhookProcessor

    processor = WebhookProcessor(password=PASSWORD)
    any_received = []

    @processor.on_any
    async def catch_all(payload: WebhookPayload):
        any_received.append(payload.Status)

    for status in ("NEW", "AUTHORIZED", "CONFIRMED"):
        raw = _build_raw_webhook({"Status": status})
        await processor.handle(raw)

    assert len(any_received) == 3


@pytest.mark.asyncio
async def test_webhook_processor_handler_exception_does_not_crash():
    """
    Если хендлер бросил исключение, processor должен вернуть OK
    (не крашиться — T-Bank не должен получить ошибку).
    """
    from TBankOA.clients import WebhookProcessor

    processor = WebhookProcessor(password=PASSWORD)

    @processor.on(PaymentStatus.AUTHORIZED)
    async def bad_handler(payload: WebhookPayload):
        raise RuntimeError("Внутренняя ошибка в хендлере")

    raw = _build_raw_webhook({"Status": "AUTHORIZED"})
    result = await processor.handle(raw)

    assert result == "OK", (
        "processor должен вернуть OK даже при исключении внутри хендлера"
    )