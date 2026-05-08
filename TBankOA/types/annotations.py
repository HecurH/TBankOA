from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer


def datetime_to_iso(dt: datetime) -> str:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Datetime must be timezone-aware")

    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()


TBankDateTime = Annotated[
    datetime,
    PlainSerializer(datetime_to_iso, when_used="json")
]