import asyncio
from datetime import datetime, timezone, timedelta
import logging
from typing import List, Literal, Optional, Type, TypeVar
import httpx

from TBankOA.exceptions import TBankOAAPIError
from TBankOA.models import *
from TBankOA.schemas import *
from TBankOA.schemas.schemas import CommonPaymentDATA

T = TypeVar("T", bound=BaseIncomingPayload)
class AsyncOnlineAcquiringClient:

    def __init__(
        self,
        terminal_key: str,
        password: str,
        base_url: str = "https://securepay.tinkoff.ru/v2", 
        http_client: httpx.AsyncClient | None = None
    ):
        self.terminal_key = terminal_key
        self.password = password
        self.base_url = base_url
        self._logger = logging.getLogger(__name__)
        self.httpx_client = http_client or httpx.AsyncClient(timeout=httpx.Timeout(15.0))

    async def close(self):
        await self.httpx_client.aclose()
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    # ── универсальный метод ───────────────────────────────────────────────────

    async def _request(
        self,
        path: str,
        info: RequestInfoModel | SignedBaseModel,
        response_model: Type[T],
    ) -> T:
        raw = await self._post(path, info)
        model = response_model(**raw.json())
        if not model.Success:
            raise TBankOAAPIError(model.ErrorCode, model.Message, model.Details)
        return model

    # ── публичные методы ──────────────────────────────────────────────────────

    async def get_payment_state(
        self, payment_id: str, ip: Optional[str] = None
    ) -> GetPaymentStateResponse:
        return await self._request(
            "/GetState",
            GetPaymentStateInfo(TerminalKey=self.terminal_key, PaymentId=payment_id, IP=ip),
            GetPaymentStateResponse,
        )

    async def get_order_state(self, order_id: str) -> GetOrderStateResponse:
        return await self._request(
            "/CheckOrder",
            GetOrderStateInfo(TerminalKey=self.terminal_key, OrderId=order_id),
            GetOrderStateResponse,
        )

    async def initialize_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        language: Optional[Literal["ru", "en"]] = "ru",
        notification_url: Optional[str] = None,
        success_url: Optional[str] = None,
        fail_url: Optional[str] = None,
        redirect_due_date: Optional[datetime] = None,
        data: Optional[CommonPaymentDATA] = None
    ) -> InitializePaymentResponse:
        return await self._request(
            "/Init",
            InitializePaymentInfo(
                TerminalKey=self.terminal_key,
                Amount=amount,
                OrderId=order_id,
                Description=description,
                Language=language,
                NotificationURL=notification_url,
                SuccessURL=success_url,
                FailURL=fail_url,
                RedirectDueDate=redirect_due_date,
                DATA=data or CommonPaymentDATA()
            ),
            InitializePaymentResponse
        )

    async def cancel_payment(
        self,
        payment_id: str,
        ip: Optional[str] = None,
        amount: Optional[int] = None,
        receipt: Optional[dict] = None,
        shops: Optional[List[dict]] = None,
        qr_member_id: Optional[str] = None,
        route: Optional[Literal["TCB", "BNPL"]] = None,
        source: Optional[Literal["installment", "BNPL"]] = None,
        external_request_id: Optional[str] = None,
    ) -> CancelPaymentResponse:
        return await self._request(
            "/Cancel",
            CancelPaymentInfo(
                TerminalKey=self.terminal_key,
                PaymentId=payment_id,
                IP=ip,
                Amount=amount,
                Receipt=receipt,
                Shops=shops,
                QrMemberId=qr_member_id,
                Route=route,
                Source=source,
                ExternalRequestId=external_request_id,
            ),
            CancelPaymentResponse,
        )

    # ── низкоуровневый транспорт ──────────────────────────────────────────────

    async def _post(
        self,
        path: str,
        model: RequestInfoModel | SignedBaseModel,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> httpx.Response:
        json_data = (
            model.get_signed_dump(self.password)
            if isinstance(model, SignedBaseModel)
            else model.dump()
        )

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await self.httpx_client.post(
                    self.base_url + path, json=json_data, **kwargs
                )
                response.raise_for_status()
                return response
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                status = getattr(exc.response, 'status_code', None) if isinstance(exc, httpx.HTTPStatusError) else None
                
                if status is not None and status < 500 and status != 429:
                    raise
                    
                last_exc = exc
                self._logger.warning(
                    "Attempt %d/%d failed: %s. Retry in %.1fs…",
                    attempt + 1, max_retries, exc, retry_delay,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2

        self._logger.error("All %d attempts failed.", max_retries)
        raise last_exc  # type: ignore[misc]
