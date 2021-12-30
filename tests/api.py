from fastapi_httpize_errors_router import HttpizeErrorsAPIRouter


router = HttpizeErrorsAPIRouter(tags=["some tag"])

@router.get("/testing", httpize_errors={ValueError: 400})
def test_route(i: int):
    if i < 1:
        raise ValueError("Bad Input Data")
    return {"i": i}



if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()
    # app.router = HttpizeErrorsAPIRouter.from_app(app)
    # app.router = HttpizeErrorsAPIRouter(
    #     routes=app.routes,
    #     dependency_overrides_provider=app,
    #     on_startup=app.router.on_startup,
    #     on_shutdown=app.router.on_shutdown,
    #     default_response_class=app.router.default_response_class,
    #     dependencies=app.router.dependencies,
    #     callbacks=app.router.callbacks,
    #     deprecated=app.router.deprecated,
    #     include_in_schema=app.router.include_in_schema,
    #     responses=app.router.responses,
    # )

    app.include_router(router)
    print(vars(app.router))

    app.setup()

    uvicorn.run(app)