"""Build a configured FastAPI application.

`create_app` is the composition root: it wires settings, the database,
error handlers and routers together. Tests call it with their own settings.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.bootstrap import seed_required_rows
from app.core.config import Settings, get_settings
from app.core.handlers import register_exception_handlers
from app.core.openapi import API_DESCRIPTION, OPENAPI_TAGS, operation_id
from app.db.session import build_engine, build_session_factory
from app.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        settings.media_dir.mkdir(parents=True, exist_ok=True)
        with session_factory() as session:
            seed_required_rows(session)
        yield
        engine.dispose()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        summary="Quotes, pricing, invoices and profit for hair extension stylists.",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        generate_unique_id_function=operation_id,
        lifespan=lifespan,
        swagger_ui_parameters={
            "docExpansion": "none",
            "defaultModelsExpandDepth": 0,
            "displayRequestDuration": True,
            "filter": True,
            "tryItOutEnabled": True,
            "persistAuthorization": True,
        },
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "Location"],
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)

    from app.core.config import PROJECT_ROOT

    frontend_dist = PROJECT_ROOT / "frontend" / "dist"
    if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        assets_dir = frontend_dist / "assets"
        if assets_dir.is_dir():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="frontend-assets",
            )

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if full_path.startswith(("v1", "docs", "redoc", "openapi.json", "health")):
                return None
            requested_file = frontend_dist / full_path
            if full_path and requested_file.is_file():
                return FileResponse(requested_file)
            return FileResponse(frontend_dist / "index.html")
    else:
        @app.get("/", include_in_schema=False)
        def root_redirect():
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/docs")

    return app
