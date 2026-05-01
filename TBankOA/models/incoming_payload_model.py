from typing import Optional

from pydantic import BaseModel

class BaseIncomingPayload(BaseModel):
    Success: bool
    """Успешность прохождения запроса"""

    ErrorCode: str = '0'
    """Код ошибки."""
    
    Message: Optional[str] = None
    """Краткое описание ошибки."""
    
    Details: Optional[str] = None
    """Подробное описание ошибки."""