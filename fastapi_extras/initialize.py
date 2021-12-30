from fastapi import FastAPI


def init_app(app: FastAPI) -> None:
    app.middleware_stack = app.build_middleware_stack()