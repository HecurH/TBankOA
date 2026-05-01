from pydantic import BaseModel

class RequestInfoModel(BaseModel):
    def dump(self) -> dict:
        return self.model_dump(exclude_none=True)