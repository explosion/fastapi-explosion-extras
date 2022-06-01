from dataclasses import dataclass
from typing import Generic, Optional, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel
from pydantic.generics import GenericModel


T = TypeVar("T")


@dataclass
class RawSeekParams:
    size: int
    regarded: T
    forward: True


class PageParams(BaseModel):
    first: Optional[int] = Query(50, ge=0)
    after: Optional[T]
    last: Optional[int] = Query(50, ge=0)
    before: Optional[T]
    forward: bool = True

    def to_raw_params(self):
        if self.forward:
            return RawSeekParams(
                size=self.first, regarded=self.after, forward=self.forward
            )
        else:
            return RawSeekParams(
                size=self.last, regarded=self.before, forward=self.forward
            )


class PageInfo(BaseModel):
    total_count: int = Query(0, ge=0)
    has_previous_page: bool = False
    has_next_page: bool = False
    start_cursor: Optional[T] = ""
    end_cursor: Optional[T] = ""

    @classmethod
    def create(
        cls, total_count, has_previous_page, has_next_page, start_cursor, end_cursor
    ):

        return cls(
            total_count=total_count,
            has_previous_page=has_previous_page,
            has_next_page=has_next_page,
            start_cursor=start_cursor,
            end_cursor=end_cursor,
        )


class Page(GenericModel, Generic[T]):
    items: Sequence[T]
    page_info: Optional[PageInfo] = None

    @classmethod
    def create_page(cls, items, total, minimum, maximum, forward):
        if len(items) == 0:
            page_info = PageInfo.create(total, False, False, "", "")
        else:
            if forward:
                has_next = items[-1].id < maximum
                has_prev = items[0].id > minimum
            else:
                has_next = items[0].id < maximum
                has_prev = items[-1].id > minimum
            page_info = PageInfo.create(
                total, has_prev, has_next, items[0].id, items[-1].id
            )

        return cls(items=items, page_info=page_info)
