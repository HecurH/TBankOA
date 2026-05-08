

from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def datetime_to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware")
    return dt.replace(microsecond=0).astimezone().isoformat() 


TBankDateTime = Annotated[
    datetime,
    PlainSerializer(datetime_to_iso, return_type=str)
]