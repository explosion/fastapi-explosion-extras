from fastapi import FastAPI, APIRouter
from fastapi_extras.initialize import init_app
from fastapi_extras.router import HttpizeErrorsAPIRouter


def test_init_app():

    app = FastAPI(title="Test App")
    assert app.title == "Test App"
    assert isinstance(app.router, APIRouter)
    assert app.router.dependency_overrides_provider == app

    init_app(app)
    assert app.title == "Test App"
    assert isinstance(app.router, HttpizeErrorsAPIRouter)
    assert app.router.dependency_overrides_provider == app
