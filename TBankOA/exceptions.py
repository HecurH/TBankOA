

from typing import Optional


class TBankOAException(Exception):
    """
    Base exception in this module.
    """
    
# api error

class TBankOAAPIError(TBankOAException):
    """
    Exception raised when API returns an error.
    """
    def __init__(self, code: str, message: Optional[str], details: Optional[str]):
        self.code = code
        self.message = message
        self.details = details
        
        super().__init__(message)
        
    def __str__(self) -> str:
        parts = [
            str(self.code) if self.code is not None else "",
            self.message if self.message is not None else "",
            self.details if self.details is not None else ""
        ]
        
        return " — ".join(filter(None, parts))
    
class TBankOAWebhookError(TBankOAException):
    """Exception raised when webhook verification or parsing fails."""