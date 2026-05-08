import json
import os

from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime

from TBankOA.models import SignedBaseModel, BaseIncomingPayload
from TBankOA.types.annotations import TBankDateTime
from TBankOA.types.enums import PaymentStatus

class CommonPaymentDATA(BaseModel):
    additionalProperties: Optional[str] = Field(default=None)
    
    OperationInitiatorType: Literal['0', '1', '2', 'R', 'I', 'D', 'N'] = Field(default='0')
    """Признак инициатора операции для платежа. Параметр обязательный при создании родительского CC-платежа при оплате картой.\n\nПодробнее о признаке инициатора операции.\n\n* 0 — обычный платеж;\n* 1 — CIT CC;\n* 2 — CIT COF;\n* R — MIT COF Recurring;\n* I — MIT COF Installment;\n* D — MIT COF Delayed-Charge;\n* N — MIT COF No-Show.\n\nЕсли передавать значения параметров, которые не соответствуют таблице, MAPI вернет ошибку 1126 — несопоставимые значения rebillId или Recurrent с переданным значением OperationInitiatorType."""

class InitializePaymentInfo(SignedBaseModel):
    TerminalKey: str
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    Amount: int
    """Сумма в копейках. Например, 3 руб. 12коп. — это число 312.\n\nПараметр должен быть равен сумме всех параметров Amount, переданных в объекте Items.\n\nМинимальная сумма операции с помощью СБП составляет 10 руб."""
    
    OrderId: str = Field(max_length=36)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
    
    Description: Optional[str] = Field(default=None, max_length=140)
    """Описание заказа. Значение параметра будет отображено на платежной форме.\n\nПараметр обязательный при привязке и одновременной оплате через СБП. При оплате через СБП текст из этого параметра отобразится в мобильном банке покупателя."""
    
    CustomerKey: Optional[str] = Field(default=None)
    """Идентификатор покупателя в системе мерчанта. Нужен для сохранения карт на платежной форме — платежи в один клик.\n\nПараметр обязательный, если передан параметр Recurrent=Y и автоплатеж проводится по карте.\n\nЕсли передан, в уведомлении будут указаны CustomerKey и его CardId. Подробнее — в методе Получить список карт покупателя."""

    Recurrent: Optional[str] = Field(default=None)
    """Признак родительского CC-платежа. Обязателен для проведения операции с сохранением реквизитов карты покупателя."""
    
    PayType: Optional[Literal['O', 'T']] = Field(default='O')
    """Определяет тип проведения платежа:\n    O — одностадийная оплата;\n    T — двухстадийная оплата.\n\nЕсли параметр передан, используется его значение, если нет — значение из настроек терминала."""

    Language: Optional[Literal['ru', 'en']] = Field(default='ru')
    """Язык платежной формы:\n\nru — русский;\n\nen — английский.\n\nЕсли параметр не передан, форма откроется на русском языке."""

    NotificationURL: Optional[str] = Field(default=None)
    """URL на веб-сайте мерчанта, куда будет отправлен POST-запрос о статусе выполнения вызываемых методов — настраивается в личном кабинете.\n\nЕсли параметр передан, используется его значение, если нет — значение из настроек терминала."""
    
    SuccessURL: Optional[str] = Field(default=None)
    """URL на веб-сайте мерчанта, куда будет переведен покупатель в случае успешной оплаты — настраивается в личном кабинете.\n\nЕсли параметр передан, используется его значение, если нет — значение из настроек терминала."""
    
    FailURL: Optional[str] = Field(default=None)
    """URL на веб-сайте мерчанта, куда будет переведен покупатель в случае неуспешной оплаты — настраивается в личном кабинете.\n\nЕсли параметр передан, используется его значение, если нет — значение из настроек терминала."""
    
    RedirectDueDate: Optional[TBankDateTime] = Field(default=None)
    """Cрок жизни ссылки или динамического QR-кода СБП, если выбран этот способ оплаты.\n\nЕсли дата в параметре меньше текущей, оплата по ссылке и QR будет недоступна.\n\n    Минимальное значение — 1 минута от текущей даты.\n    Максимальное значение — 90 дней от текущей даты.\n    Формат даты — YYYY-MM-DDTHH24:MI:SS+GMT.\nПример даты — 2016-08-31T12:28:00+03:00.\n\nЕсли параметр не был передан, проверяется настроечный параметр терминала REDIRECT_TIMEOUT, который содержит значение срока жизни ссылки в часах. Если его значение:\n\n    больше нуля — оно будет установлено в качестве срока жизни ссылки или динамического QR-кода;\n    меньше нуля — устанавливается значение по умолчанию: 1440 мин. (1 сутки)."""
    
    DATA: CommonPaymentDATA = Field(default=CommonPaymentDATA())
    
    Receipt: Optional[dict] = Field(default=None)
    
    Shops: Optional[List[dict]] = Field(default=None)
    
class InitializePaymentResponse(BaseIncomingPayload):
    TerminalKey: Optional[str] = Field(default=None)
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    Amount: Optional[int] = Field(default=None)
    """Сумма в копейках. Например, 3 руб. 12коп. — это число 312.\n\nПараметр должен быть равен сумме всех параметров Amount, переданных в объекте Items.\n\nМинимальная сумма операции с помощью СБП составляет 10 руб."""
    
    OrderId: Optional[str] = Field(default=None)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
    
    Status: Optional[PaymentStatus] = Field(default=None)
    """Статус транзакции."""
    
    PaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    PaymentURL: Optional[str] = Field(default=None)
    """Ссылка на платежную форму. Параметр возвращается только для мерчантов, которые используют платежную форму Т-Банка."""


class CancelPaymentInfo(SignedBaseModel):
    TerminalKey: str
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    PaymentId: str
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    IP: Optional[str] = Field(default=None)
    
    Amount: Optional[int] = Field(default=None)
    """Сумма в копейках. Если не передан, используется Amount, переданный в методе Инициировать платеж.\n\nПри отмене операции в статусе NEW поле Amount игнорируется, даже если оно заполнено. Отмена проводится на полную сумму."""
    
    Receipt: Optional[dict] = Field(default=None)
    
    Shops: Optional[List[dict]] = Field(default=None)
    
    QrMemberId: Optional[str] = Field(default=None)
    """Код банка в классификации СБП, в который нужно выполнить возврат.\n\nПодробнее — в параметре MemberId метода Получить список банков-пользователей QR."""
    
    Route: Optional[Literal['TCB', 'BNPL']] = Field(default=None)
    """Способ платежа."""
    
    Source: Optional[Literal['installment', 'BNPL']] = Field(default=None)
    """Источник платежа."""
    
    ExternalRequestId: Optional[str] = Field(default=None)
    """Идентификатор операции на стороне мерчанта.\n\nПараметр обязательный для операций «Долями» и в рассрочку.\n  - Если поле не передано или пустое (""), запрос будет обработан без проверки ранее созданных возвратов.\n  - Если поле заполнено, перед проведением возврата будет проверен запрос на отмену с таким ExternalRequestId.\n  - Если такой запрос уже есть, в ответе вернется текущее состояние платежной операции, если нет — платеж будет отменен.\n  - Для операций «Долями» при заполнении параметра нужно генерировать значение в формате UUID v4.\n  - Для операций в рассрочку при заполнении параметра нужно генерировать значение с типом string — ограничение 100 символов.\n  - Для способа оплаты AlfaPay при заполнении параметра ExternalRequestId длина значения не должна превышать 36 символов."""

class CancelPaymentResponse(BaseIncomingPayload):
    TerminalKey: Optional[str] = Field(default=None)
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    OrderId: Optional[str] = Field(default=None)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
    
    Status: Optional[PaymentStatus] = Field(default=None)
    """Статус транзакции."""
    
    OriginalAmount: Optional[int] = Field(default=None)
    """Сумма в копейках до операции отмены."""
    
    NewAmount: Optional[int] = Field(default=None)
    """Сумма в копейках после операции отмены."""
    
    PaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    ExternalRequestId: Optional[str] = Field(default=None)
    """Идентификатор операции на стороне мерчанта."""
    
class GetPaymentStateInfo(SignedBaseModel):
    TerminalKey: str
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""

    PaymentId: str
    """Идентификатор платежа в системе Т‑Бизнес."""

    IP: Optional[str] = Field(default=None)
    
class PaymentStateParam(BaseModel):
    Key: Optional[Literal["Route", "Source", "CreditAmount"]]
    """* Route — способ оплаты.\n* Source — источник платежа.\n* CreditAmount — сумма выданного кредита в копейках. Возвращается только для платежей в рассрочку."""
    
    Value: Optional[Literal["ACQ", "BNPL", "TCB", "SBER", "BNPL", 
                            "cards", "Installment", "MirPay", "qrsbp", "SberPay", "TinkoffPay", "YandexPay"] | int]
    """* для Route — ACQ, BNPL, TCB, SBER;\n* для Source — BNPL, cards, Installment, MirPay, qrsbp, SberPay, TinkoffPay, YandexPay;\n* для CreditAmount — сумма в копейках."""

class GetPaymentStateResponse(BaseIncomingPayload):
    TerminalKey: Optional[str] = Field(default=None)
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    Amount: Optional[int] = Field(default=None)
    """Сумма в копейках."""

    OrderId: Optional[str] = Field(default=None)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
        
    Status: Optional[PaymentStatus] = Field(default=None)
    """Статус платежа."""
    
    PaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    Params: Optional[List[Optional[PaymentStateParam]]] = Field(default=None)
    """Параметры платежа."""
    
class GetOrderStateInfo(SignedBaseModel):
    TerminalKey: str
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""

    OrderId: str
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""

class PaymentOrderEntry(BaseIncomingPayload):
    PaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    Amount: Optional[int] = Field(default=None)
    """Сумма в копейках."""
    
    Status: Optional[PaymentStatus] = Field(default=None)
    """Статус операции."""
    
    RRN: Optional[str] = Field(default=None)
    """RRN операции."""
    
    SbpPaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в СБП."""

    SbpCustomerId: Optional[str] = Field(default=None)
    """Хэшированный номер телефона покупателя."""

class GetOrderStateResponse(BaseIncomingPayload):
    TerminalKey: Optional[str] = Field(default=None)
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""

    OrderId: Optional[str] = Field(default=None)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
    
    Payments: Optional[List[Optional[PaymentOrderEntry]]] = Field(default=None)
    """Параметры платежа."""
    
class WebhookPayload(BaseIncomingPayload, SignedBaseModel):
    TerminalKey: Optional[str] = Field(default=None)
    """Идентификатор терминала. Выдается мерчанту в Т‑Бизнес при заведении терминала."""
    
    Amount: Optional[int] = Field(default=None)
    """Сумма в копейках."""
    
    OrderId: Optional[str] = Field(default=None)
    """Идентификатор заказа в системе мерчанта. Должен быть уникальным для каждой операции."""
    
    Status: Optional[PaymentStatus] = Field(default=None)
    """Статус платежа."""
    
    PaymentId: Optional[str] = Field(default=None)
    """Идентификатор платежа в системе Т‑Бизнес."""
    
    RebillId: Optional[int] = Field(default=None)
    """Уникальный идентификатор сохраненных реквизитов карты покупателя."""
    
    CardId: Optional[int] = Field(default=None)
    """Идентификатор карты в системе Т‑Бизнес. Если в Pan указан номер телефона, параметр в уведомлении может отсутствовать."""
    
    Pan: Optional[str] = Field(default=None)
    """Замаскированный номер карты или телефона."""
    
    ExpDate: Optional[str] = Field(default=None)
    """Срок действия карты в формате MMYY.\n- Параметр возвращается пустым для привязок с "CheckType": "NO".\n- Если в Pan указан номер телефона, параметр в уведомлении может отсутствовать."""
    
    Data: Optional[List[Optional[PaymentStateParam]]] = Field(default=None)
    """Дополнительные параметры платежа, которые передаются при создании заказа. Являются обязательными для платежей в рассрочку. В ответе возвращается параметр Data — учитывайте регистр."""
    
