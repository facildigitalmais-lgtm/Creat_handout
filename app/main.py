from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.paths import (
    STATIC_DIR,
    ensure_runtime_directories,
)
from app.core.settings import get_settings
from app.services.subject_catalog import subject_catalog_service


settings = get_settings()


logging.basicConfig(
    level=(
        logging.DEBUG
        if settings.debug
        else logging.INFO
    ),
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "apostila_builder"
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    ensure_runtime_directories()

    logger.info(
        "Carregando biblioteca de matérias..."
    )

    snapshot = subject_catalog_service.reload()

    app.state.subject_catalog_service = (
        subject_catalog_service
    )

    logger.info(
        (
            "Biblioteca de matérias carregada: "
            "%s arquivo(s), "
            "%s válido(s), "
            "%s inválido(s), "
            "%s matéria(s)."
        ),
        snapshot["estatisticas"]["arquivos"],
        snapshot["estatisticas"]["validos"],
        snapshot["estatisticas"]["invalidos"],
        snapshot["estatisticas"]["materias"],
    )

    yield

    logger.info(
        "Aplicação encerrada."
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(
        directory=str(STATIC_DIR),
    ),
    name="static",
)

app.include_router(router)