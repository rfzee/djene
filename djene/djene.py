from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Generic, Type, TypeVar

from fastapi import Request
from sqlmodel import Session, SQLModel
from starlette.middleware.base import BaseHTTPMiddleware

from djene.queryset import DjQuery

T = TypeVar("T", bound=SQLModel)


class Djene(Generic[T]):
    _session_ctx_var: ContextVar[Session] = ContextVar("_djene_session_ctx")
    _engine = None

    def __init__(self, model: Type[T]):
        self.model = model

    def __getattr__(self, name: str) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            session = Djene.get_session()
            queryset = DjQuery(self.model, session)
            method = getattr(queryset, name)
            return method(*args, **kwargs)

        return wrapper

    @classmethod
    def set_engine(cls, engine):
        cls._engine = engine

    @classmethod
    def get_engine(cls):
        return cls._engine

    @classmethod
    def register(cls, session: Session) -> Token:
        return cls._session_ctx_var.set(session)

    @classmethod
    def dispose(cls, token: Token):
        cls._session_ctx_var.reset(token)

    @classmethod
    def get_session(cls) -> Session:
        session = cls._session_ctx_var.get()
        if session is not None:
            return session

        raise ValueError(
            "No session found in context. Use Djene.create_session() or middleware."
        )

    @classmethod
    @contextmanager
    def create_session(cls):
        if cls._engine is None:
            raise ValueError("Engine not configured. Call Djene.set_engine() first.")

        print("creating session")
        with Session(cls._engine) as session:
            token: Token = cls.register(session)
            try:
                yield session
            finally:
                session.commit()
                cls.dispose(token)


def dj(model):
    return Djene(model)


class DjeneMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, engine):
        super().__init__(app)
        Djene.set_engine(engine)
        _id = id(self)

    async def dispatch(self, request: Request, call_next):
        print("dispatching")
        print(request)

        with Djene.create_session() as session:
            # token: Token = Djene.register(self._id, session)
            token: Token = Djene.register(session)

            try:
                response = await call_next(request)
            finally:
                Djene.dispose(token)
        return response
