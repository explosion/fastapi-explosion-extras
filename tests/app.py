from fastapi_extras import HttpizeErrorsAPIRouter, HttpizeErrorsAPIRoute
from tests.api import router


if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()
    # app.router = HttpizeErrorsAPIRouter.from_app(app)
    main_router = HttpizeErrorsAPIRouter(
        routes=app.routes,
        dependency_overrides_provider=app,
        on_startup=app.router.on_startup,
        on_shutdown=app.router.on_shutdown,
        default_response_class=app.router.default_response_class,
        dependencies=app.router.dependencies,
        callbacks=app.router.callbacks,
        deprecated=app.router.deprecated,
        include_in_schema=app.router.include_in_schema,
        responses=app.router.responses,
    )

    # app.router.route_class = HttpizeErrorsAPIRoute

    # api_router = HttpizeErrorsAPIRouter(prefix="/api")
    # api_router.include_router(router)

    app.router = main_router
    app.include_router(router)
    print(vars(app.router))

    @app.get("/other_test")
    def other_test():
        return {"status": "ok"}

    uvicorn.run(app)