from datetime import datetime, timezone, timedelta
import logging
from typing import Awaitable, Callable, List, Literal, Optional, Type, TypeVar

from TBankOA.exceptions import TBankOAWebhookError
from TBankOA.models import *
from TBankOA.schemas import *
from TBankOA.types.enums import PaymentStatus

Handler = Callable[[WebhookPayload], Awaitable[None]]

class WebhookProcessor:
       
    def __init__(self, password: str):
        self._password = password
        self._logger = logging.getLogger(__name__)

        # status → список хендлеров
        self._handlers: dict[str, list[Handler]] = {}
        # хендлеры на любой статус
        self._any_handlers: list[Handler] = []

    # ── Регистрация хендлеров ────────────────────────────────────────────────

    def on(self, *statuses: PaymentStatus):
        """
        Декоратор: подписаться на конкретные статусы.

            @processor.on(PaymentStatus.NEW, PaymentStatus.CONFIRMED)
            async def handle(payload: WebhookPayload) -> None:
                ...
        """
        def decorator(fn: Handler) -> Handler:
            for status in statuses:
                self._handlers.setdefault(status.value, []).append(fn)
            return fn
        return decorator

    def on_any(self, fn: Handler) -> Handler:
        """Подписаться на все статусы."""
        self._any_handlers.append(fn)
        return fn

    # ── Основной метод ───────────────────────────────────────────────────────

    async def handle(self, data: dict) -> str:
        """
        Принимает сырой dict из тела запроса.
        Возвращает строку-ответ, которую нужно отдать TBank ("OK" или сообщение об ошибке).

        Пример во views (aiohttp):
            payload = await request.json()
            response_text = await processor.handle(payload)
            return web.Response(text=response_text)
        """
        try:
            payload = WebhookPayload(**data)
            if not payload.verify_signature(self._password):
                raise TBankOAWebhookError("Invalid signature")
            
        except Exception as e:
            self._logger.error("Webhook payload parse error: %s | raw: %s", e, data)
            return "FAIL"

        await self._dispatch(payload)
        return "OK"

    # ── Внутренние методы ────────────────────────────────────────────────────

    async def _dispatch(self, payload: WebhookPayload) -> None:
        status = payload.Status.value if payload.Status else "any"
        handlers = [*self._handlers.get(status, []), *self._any_handlers]

        if not handlers:
            self._logger.debug("No handlers for status %r (PaymentId=%s)", status, payload.PaymentId)
            return

        for handler in handlers:
            try:
                await handler(payload)
            except Exception:
                self._logger.exception(
                    "Handler %r raised an exception for PaymentId=%s status=%s",
                    handler.__name__, payload.PaymentId, status,
                )