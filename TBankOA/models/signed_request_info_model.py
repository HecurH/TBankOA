from pydantic import Field

from .request_info_model import RequestInfoModel

from TBankOA.tools import generate_signature, verify_signature


class SignedBaseModel(RequestInfoModel):
    Token: str = Field(default="", repr=False)
    
    def _sign(self, password: str):
        json = self.model_dump(mode="json", exclude={'Token'}, exclude_none=True)
        signature = generate_signature(json, password)
        self.Token = signature
    
    def get_signed_dump(self, password: str) -> dict:
        self._sign(password)
        return self.dump()
    
    def verify_signature(self, password: str) -> bool:        
        json = self.model_dump(mode="json", exclude={'Token'}, exclude_none=True)
        return verify_signature(json, password, self.Token)