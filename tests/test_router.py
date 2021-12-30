import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from fastapi_extras import HttpizeErrorsAPIRoute, HttpizeErrorsAPIRouter
from starlette import routing

from .api import router as api_router


def test_router_init():
    router = HttpizeErrorsAPIRouter(tags=["some tag"])
    assert isinstance(router, APIRouter)
    assert router.tags == ["some tag"]

    app = FastAPI()
    assert not isinstance(app.router, HttpizeErrorsAPIRouter)
    app.router = router
    assert isinstance(app.router, HttpizeErrorsAPIRouter)


def test_route_definition():
    app = FastAPI()
    app.include_router(api_router)

    client = TestClient(app)

    res = client.get("testing", params={"i": 1})
    assert res.status_code == 200

    with pytest.raises(ValueError):
        res = client.get("testing", params={"i": -1})


def test_route_definition_app_router_included():
    app = FastAPI()
    app.router = HttpizeErrorsAPIRouter.from_app(app)
    
    app.include_router(api_router)

    print(vars(app.routes[-1]))

    assert isinstance(app.routes[-1], routing.Route)

    client = TestClient(app)

    res = client.get("/openapi.json", params={"i": 1})
    assert res.status_code == 200

    print(res.json())

    res = client.get("testing", params={"i": 1})
    print(res.json())
    assert res.status_code == 200

    print(client.app.routes)
    res = client.get("testing", params={"i": -1})
    assert res.status_code == 400