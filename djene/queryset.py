from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, List, Optional, Type, TypeVar

from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlmodel import Session, SQLModel, delete, select, update

T = TypeVar("T", bound="SQLModel")


@dataclass
class LookupField:
    field_name: str
    lookup: str
    value: Any
    exclude: bool


class QueryDescriptor[T]:
    def __init__(self, session: Session):
        self.items_cache = None
        self.session = session

    def __iter__(self) -> Iterator[T]:
        return iter(self._execute_if_needed())

    def __len__(self) -> int:
        return len(self._execute_if_needed())

    def __bool__(self) -> bool:
        return bool(self._execute_if_needed())

    def __bool__(self) -> bool:
        return bool(self._execute_if_needed())

    def __getitem__(self, index):
        self._execute_if_needed()
        return self.items_cache[index]

    def _execute_if_needed(self):
        if self.items_cache is None:
            self._select()

        return self.items_cache


class DjQuery[T](QueryDescriptor):
    def __init__(self, model: Type[T], session: Session):
        super().__init__(session=session)
        self.model = model
        self.session = session
        self.query = select(model)
        self.lookup_filters: List[LookupField] = []

    def _clone(self) -> DjQuery[T]:
        qs = DjQuery(self.model, self.session)
        qs.query = self.query
        qs.lookup_filters = self.lookup_filters.copy()
        return qs

    def compile_conditions(self) -> List[Any]:
        conditions = []
        for lookup in self.lookup_filters:
            column = getattr(self.model, lookup.field_name, None)

            if column is None:
                breakpoint()
                raise AttributeError(f"{lookup.field_name} is not a valid field name.")

            lookup_name = lookup.lookup
            filter_expr = self._resolve_lookup(column, lookup_name, lookup.value)
            if lookup.exclude:
                filter_expr = ~filter_expr
            conditions.append(filter_expr)
        return conditions

    def _resolve_lookup(self, column, lookup_name, value):
        if lookup_name == "eq":
            return column == value
        elif lookup_name == "gt":
            return column > value
        elif lookup_name == "gte":
            return column >= value
        elif lookup_name == "lt":
            return column < value
        elif lookup_name == "lte":
            return column <= value
        elif lookup_name == "in":
            return column.in_(value)
        elif lookup_name == "isnull":
            return column.is_(None) if value else column.isnot(None)
        elif lookup_name == "range":
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(
                    "`range` lookup requires a tuple or list with exactly two elements."
                )
            return column.between(value[0], value[1])
        else:
            return getattr(column, lookup_name)(value)

    def _mount_filters(self):
        conditions = self.compile_conditions()
        self.query = self.query.filter(*conditions)

    def _select(self):
        self._mount_filters()
        self.items_cache = self.session.exec(self.query).all()

    def _apply_filter(self, exclude=False, **kwargs) -> DjQuery[T]:
        cloned_qs = self._clone()

        lookups = [
            "eq",
            "like",
            "ilike",
            "contains",
            "startswith",
            "endswith",
            "gt",
            "lt",
            "gte",
            "lte",
            "isnull",
            "in",
            "between",
        ]

        for key, val in kwargs.items():
            self._append_lookup(cloned_qs, key, val, exclude, lookups)

        return cloned_qs

    def _append_lookup(self, cloned_qs, key, val, exclude, lookups):
        parts = key.split("__")
        field_name = parts[0]
        lookup = parts[1] if len(parts) > 1 else "eq"
        if lookup not in lookups:
            raise ValueError(f"Unsupported lookup filter: {lookup}")

        cloned_qs.lookup_filters.append(LookupField(field_name, lookup, val, exclude))

    def all(self) -> DjQuery[T]:
        return self._clone()

    def first(self) -> None | T:
        if not self.items_cache:
            self._select()
        try:
            return self.items_cache[0]
        except IndexError:
            return None

    def limit(self, limit: int) -> DjQuery[T]:
        """Limits the number of results returned by the query."""
        cloned_qs = self._clone()
        cloned_qs.query = cloned_qs.query.limit(limit)
        return cloned_qs

    def offset(self, offset: int) -> DjQuery[T]:
        """Skips the specified number of results before starting to return rows."""
        cloned_qs = self._clone()
        cloned_qs.query = cloned_qs.query.offset(offset)
        return cloned_qs

    def last(self) -> None | T:
        if not self.items_cache:
            self._select()
        return self.items_cache[-1] if self.items_cache else None

    def order_by(self, *fields: str) -> DjQuery[T]:
        cloned_qs = self._clone()
        for field in fields:
            if not hasattr(self.model, field):
                raise ValueError(f"Invalid field for ordering: {field}")
            cloned_qs.query = cloned_qs.query.order_by(getattr(self.model, field))
        return cloned_qs

    def filter(self, **kwargs) -> DjQuery[T]:
        return self._apply_filter(**kwargs)

    def where(self, **kwargs) -> DjQuery[T]:
        return self.filter(**kwargs)

    def exclude(self, **kwargs) -> DjQuery[T]:
        return self._apply_filter(exclude=True, **kwargs)

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        return obj

    def delete(self, **kwargs) -> None:
        conditions = self.compile_conditions()
        delete_query = delete(self.model).filter(*conditions)

        self.session.exec(delete_query)

    def update(self, **kwargs) -> None:
        conditions = self.compile_conditions()
        update_query = update(self.model).filter(*conditions).values(**kwargs)

        self.session.exec(update_query)

    def get_or_none(self, **kwargs) -> T | None:
        try:
            return self.filter(**kwargs).first()
        except NoResultFound:
            return None

    def get(self, **kwargs) -> Optional[T]:
        qs = self.filter(**kwargs)
        entity = qs.first()
        if not entity:
            raise NoResultFound("No results found.")

        if qs.items_cache and len(qs.items_cache) > 1:
            raise MultipleResultsFound("Multiple results returned for `get`.")

        return entity
