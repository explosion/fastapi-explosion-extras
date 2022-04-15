from fastapi_explosion_extras import HttpizeErrorsAPIRouter, init_app


router = HttpizeErrorsAPIRouter(tags=["some tag"])

@router.get("/testing", httpize_errors={ValueError: 400})
def test_route(i: int):
    if i < 1:
        raise ValueError("Bad Input Data")
    return {"i": i}


class SpecError(ValueError):
    pass


@router.get("/testing_specific", httpize_errors={SpecError: 400})
def test_route_specific(i: int):
    if i < 1:
        raise SpecError("Bad Input Data")
    return {"i": i}


if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn

    app = FastAPI()
    app.router = HttpizeErrorsAPIRouter.from_app(app)
    app.include_router(router)
    init_app(app)

    @app.get("/other_test")
    def test_route(message: str):
        return message

    uvicorn.run(app)