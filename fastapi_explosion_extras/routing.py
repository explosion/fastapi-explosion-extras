import time
import traceback
from logging import Logger
from typing import Any, Callable, Coroutine, Dict, List, Optional, Sequence, Set, Type, Union

from pyparsing import empty

from fastapi import HTTPException, Request, Response, params
from fastapi.applications import FastAPI
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.encoders import DictIntStrAny, SetIntStr
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, APIRouter, APIWebSocketRoute
from fastapi.types import DecoratedCallable
from fastapi.utils import get_value_or_default
from starlette import routing
from starlette.routing import BaseRoute

from .types import ErrorsType, ResponsesType, _ReturnT


class HttpizeErrorsAPIRoute(APIRoute):
    """HttpizeErrorsAPIRoute overrides default FastAPI behavior to
    add common Response error types and set the OpenAPI operation_id
    to the name of the decorated route function."""
    logger: Optional[Logger] = None

    def __init__(
        self,
        *args,
        httpize_errors: Optional[ErrorsType] = None,
        logger: Optional[Logger] = None,
        empty_response: Response = Response(status_code=204),
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.httpize_errors = httpize_errors or {}
        self.operation_id = self.name
        self.logger = HttpizeErrorsAPIRoute.logger or logger
        self.empty_response = empty_response

    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            error_types = tuple(self.httpize_errors.keys())
            try:
                before = time.time()
                response: Response = await original_route_handler(request)
                duration = time.time() - before
                response.headers["X-Response-Time"] = str(duration)
                if self.logger:
                    self.logger.debug(f"route duration: {duration}")
                    self.logger.debug(f"route response: {response}")
            except error_types as e:  # type: ignore
                if self.logger:
                    self.logger.error("\n".join(traceback.format_tb(e.__traceback__)))
                    self.logger.error(str(e))

                # If the error is one that we want to catch, return a
                # consistent response with the Error type so it can
                # be reversed by the PAM SDK
                value = self.httpize_errors[e.__class__]
                if isinstance(value, int):
                    code = value
                    message = getattr(e, "detail", str(e))
                elif isinstance(value, tuple) and len(value) == 2:
                    code, message = value
                else:
                    # If we're here, we messed up somewhere! But we probably
                    # don't want to crash the app.
                    code = 500
                    message = "error in error-handling logic"
                detail = {
                    "message": message,
                    "type": e.__class__.__name__.replace("_", ""),
                }
                raise HTTPException(status_code=code, detail=detail) from None
            except Exception as e:
                if self.logger:
                    self.logger.error("\n".join(traceback.format_tb(e.__traceback__)))
                raise e
            else:
                if response is None or getattr(response, "body", None) == b"null":
                    # Return an empty response instead of None/null for delete requests
                    return self.empty_response
                else:
                    return response

        return custom_route_handler


class HttpizeErrorsAPIRouter(APIRouter):
    """Custom Router that implements the `httpize_errors` argument to convert
    per route errors to HTTPException errors that FastAPI knows how to return"""

    @classmethod
    def from_app(cls, app: FastAPI):
        router = cls(
            routes=app.router.routes,
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
        return router

    def __init__(self, *args, logger: Optional[Logger] = None, **kwargs):
        super().__init__(*args, **kwargs)
        route_class = HttpizeErrorsAPIRoute
        if logger is not None:
            route_class.logger = logger
        self.route_class = route_class

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        httpize_errors: Optional[ErrorsType] = None,
        response_model: Optional[Type[Any]] = None,
        status_code: Optional[int] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        name: Optional[str] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        route_class = self.route_class
        responses = responses or {}
        combined_responses = {**self.responses, **responses}
        current_response_class = get_value_or_default(
            response_class, self.default_response_class
        )
        current_tags = self.tags.copy()
        if tags:
            current_tags.extend(tags)
        current_dependencies = self.dependencies.copy()
        if dependencies:
            current_dependencies.extend(dependencies)
        current_callbacks = self.callbacks.copy()
        if callbacks:
            current_callbacks.extend(callbacks)
        route = route_class(
            self.prefix + path,
            httpize_errors=httpize_errors,
            endpoint=endpoint,
            response_model=response_model,
            status_code=status_code,
            tags=current_tags,
            dependencies=current_dependencies,
            summary=summary,
            description=description,
            response_description=response_description,
            responses=combined_responses,
            deprecated=deprecated or self.deprecated,
            methods=methods,
            operation_id=operation_id,
            response_model_include=response_model_include,
            response_model_exclude=response_model_exclude,
            response_model_by_alias=response_model_by_alias,
            response_model_exclude_unset=response_model_exclude_unset,
            response_model_exclude_defaults=response_model_exclude_defaults,
            response_model_exclude_none=response_model_exclude_none,
            include_in_schema=include_in_schema and self.include_in_schema,
            response_class=current_response_class,
            name=name,
            dependency_overrides_provider=self.dependency_overrides_provider,
            callbacks=current_callbacks,
            openapi_extra=openapi_extra,
        )
        self.routes.append(route)

    def api_route(
        self, path: str, *, httpize_errors: Optional[ErrorsType] = None, **kwargs
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_api_route(path, func, httpize_errors=httpize_errors, **kwargs)
            return func

        return decorator

    def include_router(
        self,
        router: "HttpizeErrorsAPIRouter",
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
    ) -> None:
        if prefix:
            assert prefix.startswith("/"), "A path prefix must start with '/'"
            assert not prefix.endswith(
                "/"
            ), "A path prefix must not end with '/', as the routes will start with '/'"
        else:
            for r in router.routes:
                path = getattr(r, "path")
                name = getattr(r, "name", "unknown")
                if path is not None and not path:
                    raise Exception(
                        f"Prefix and path cannot be both empty (path operation: {name})"
                    )
        if responses is None:
            responses = {}
        for route in router.routes:
            if isinstance(route, APIRoute):
                combined_responses = {**responses, **route.responses}
                use_response_class = get_value_or_default(
                    route.response_class,
                    router.default_response_class,
                    default_response_class,
                    self.default_response_class,
                )
                current_tags = []
                if tags:
                    current_tags.extend(tags)
                if route.tags:
                    current_tags.extend(route.tags)
                current_dependencies: List[params.Depends] = []
                if dependencies:
                    current_dependencies.extend(dependencies)
                if route.dependencies:
                    current_dependencies.extend(route.dependencies)
                current_callbacks = []
                if callbacks:
                    current_callbacks.extend(callbacks)
                if route.callbacks:
                    current_callbacks.extend(route.callbacks)
                kwargs = dict(
                    response_model=route.response_model,
                    status_code=route.status_code,
                    tags=current_tags,
                    dependencies=current_dependencies,
                    summary=route.summary,
                    description=route.description,
                    response_description=route.response_description,
                    responses=combined_responses,
                    deprecated=route.deprecated or deprecated or self.deprecated,
                    methods=route.methods,
                    operation_id=route.operation_id,
                    response_model_include=route.response_model_include,
                    response_model_exclude=route.response_model_exclude,
                    response_model_by_alias=route.response_model_by_alias,
                    response_model_exclude_unset=route.response_model_exclude_unset,
                    response_model_exclude_defaults=route.response_model_exclude_defaults,
                    response_model_exclude_none=route.response_model_exclude_none,
                    include_in_schema=route.include_in_schema
                    and self.include_in_schema
                    and include_in_schema,
                    response_class=use_response_class,
                    name=route.name,
                    callbacks=current_callbacks,
                    openapi_extra=route.openapi_extra,
                )
                if isinstance(route, HttpizeErrorsAPIRoute):
                    kwargs["httpize_errors"] = route.httpize_errors  # type: ignore
                self.add_api_route( 
                    prefix + route.path, route.endpoint, **kwargs  # type: ignore
                )

            elif isinstance(route, routing.Route):
                methods = list(route.methods or [])  # type: ignore # in Starlette
                self.add_route(
                    prefix + route.path,
                    route.endpoint,
                    methods=methods,
                    include_in_schema=route.include_in_schema,
                    name=route.name,
                )
            elif isinstance(route, APIWebSocketRoute):
                self.add_api_websocket_route(
                    prefix + route.path, route.endpoint, name=route.name
                )
            elif isinstance(route, routing.WebSocketRoute):
                self.add_websocket_route(
                    prefix + route.path, route.endpoint, name=route.name
                )
        for handler in router.on_startup:
            self.add_event_handler("startup", handler)
        for handler in router.on_shutdown:
            self.add_event_handler("shutdown", handler)

    def get(
        self, path: str, *, httpize_errors: Optional[ErrorsType] = None, **kwargs
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.api_route(
            path=path, httpize_errors=httpize_errors, methods=["GET"], **kwargs
        )

    def put(
        self, path: str, *, httpize_errors: Optional[ErrorsType] = None, **kwargs
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.api_route(
            path=path, httpize_errors=httpize_errors, methods=["PUT"], **kwargs
        )

    def post(
        self, path: str, *, httpize_errors: Optional[ErrorsType] = None, **kwargs
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.api_route(
            path=path, httpize_errors=httpize_errors, methods=["POST"], **kwargs
        )

    def delete(
        self, path: str, *, httpize_errors: Optional[ErrorsType] = None, **kwargs
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self.api_route(
            path=path, httpize_errors=httpize_errors, methods=["DELETE"], **kwargs
        )
