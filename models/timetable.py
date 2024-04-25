import datetime
from typing import List

from pydantic import BaseModel, Field


class Interval(BaseModel):
    start: datetime.time
    end: datetime.time

    def is_in_interval(self, time: datetime.time):
        return self.start <= time <= self.end

    @classmethod
    def full_time(cls):
        return cls(start=datetime.time(0), end=datetime.time(23, 59, 59, 999999))

    @classmethod
    def full_time_list(cls):
        return [cls.full_time()]


class Timetable(BaseModel):
    mon: List[Interval] = Field(default_factory=Interval.full_time)
    tue: List[Interval] = Field(default_factory=Interval.full_time)
    wed: List[Interval] = Field(default_factory=Interval.full_time)
    thu: List[Interval] = Field(default_factory=Interval.full_time)
    fri: List[Interval] = Field(default_factory=Interval.full_time)
    sat: List[Interval] = Field(default_factory=Interval.full_time)
    sun: List[Interval] = Field(default_factory=Interval.full_time)

    def is_in_timetable(self, dt: datetime.datetime):
        intervals = {
            0: self.mon,
            1: self.tue,
            2: self.wed,
            3: self.thu,
            4: self.fri,
            5: self.sat,
            6: self.sun
        }[dt.weekday()]
        return any((interval.is_in_interval(dt.time()) for interval in intervals))
