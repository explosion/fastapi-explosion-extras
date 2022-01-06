from fastapi import FastAPI
from .routing import HttpizeErrorsAPIRouter


def init_app(app: FastAPI) -> None:
    app.router = HttpizeErrorsAPIRouter.from_app(app)
    app.middleware_stack = app.build_middleware_stack()
    return app
