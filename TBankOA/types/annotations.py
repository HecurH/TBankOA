

from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def datetime_to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    
    return dt.replace(microsecond=0).astimezone().isoformat() 


TBankDateTime = Annotated[
    datetime,
    PlainSerializer(datetime_to_iso, return_type=str)
]