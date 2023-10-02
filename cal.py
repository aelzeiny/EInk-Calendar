import datetime as dt
from typing import Tuple, Union
import icalendar
import requests
import pytz
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import pickle


@dataclass
class CalEvent:
    summary: str
    start_dttm: dt.datetime
    end_dttm: dt.datetime
    status: str


CAL_SUMMARY = 'SUMMARY'
CAL_START = 'DTSTART'
CAL_END = 'DTEND'
CAL_STATUS = 'STATUS'
TZ = pytz.timezone('America/Los_Angeles')


def date_to_end_dttm(dttm: Union[dt.date, dt.datetime]):
    if isinstance(dttm, dt.datetime):
        return dttm
    return dt.datetime.combine(dttm, dt.datetime.max.time(), tzinfo=TZ)


def date_to_beg_dttm(dttm: Union[dt.date, dt.datetime]):
    if isinstance(dttm, dt.datetime):
        return dttm
    return dt.datetime.combine(dttm, dt.datetime.min.time(), tzinfo=TZ)


def hardcoded_events() -> list[CalEvent]:
    return [
        CalEvent(
            summary="Lunch time",
            start_dttm=dt.datetime.combine(dt.date.today(), dt.time(12, 0), tzinfo=TZ),
            end_dttm=dt.datetime.combine(dt.date.today(), dt.time(13, 0), tzinfo=TZ),
            status="CONFIRMED"
        ),
        CalEvent(
            summary="Sleep",
            start_dttm=dt.datetime.combine(dt.date.today(), dt.time(23, 59), tzinfo=TZ),
            end_dttm=dt.datetime.combine(dt.date.today() + dt.timedelta(days=1), dt.time(9, 0), tzinfo=TZ),
            status="CONFIRMED"
        ),
    ]

def get_next_events(calendar: icalendar.Calendar) -> Tuple[CalEvent, CalEvent]:
    events = [
        CalEvent(
            summary=str(event.get(CAL_SUMMARY)),
            start_dttm=date_to_beg_dttm(event.get(CAL_START).dt),
            end_dttm=date_to_end_dttm(event.get(CAL_END).dt),
            status=str(event.get(CAL_STATUS)),
        )
        for event in calendar.walk('VEVENT')
    ]
    events.extend(hardcoded_events())
    now = dt.datetime.now(pytz.utc)
    after_events = sorted([e for e in events if e.start_dttm > now], key=lambda e: e.start_dttm)
    inside_events = sorted([e for e in events if e.start_dttm >= now and e.end_dttm < now], key=lambda e: -e.end_dttm.timestamp())
    return after_events, inside_events
