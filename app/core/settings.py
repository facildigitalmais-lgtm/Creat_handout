from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.paths import PROJECT_ROOT, SETTINGS_FILE


@dataclass(frozen=True, slots=True)
class EditorSettings:
    nome: str
    site: str


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_version: str
    host: str
    port: int
    debug: bool
    library_dir: Path
    schema_file: Path
    prompt_template_file: Path
    projects_dir: Path
    uploads_dir: Path
    temp_dir: Path
    output_dir: Path
    editor: EditorSettings


def _resolve_project_path(value: str) -> Path:
    path = Path(value)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def _read_settings_file() -> dict[str, Any]:
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração não encontrado: {SETTINGS_FILE}"
        )

    with SETTINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "O arquivo config/settings.json deve conter um objeto JSON."
        )

    return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    data = _read_settings_file()

    editor_data = data.get("editor") or {}

    return Settings(
        app_name=str(
            data.get(
                "app_name",
                "Fácil Digital+ — Montador de Apostilas",
            )
        ),
        app_version=str(data.get("app_version", "0.1.0")),
        host=str(data.get("host", "0.0.0.0")),
        port=int(data.get("port", 8000)),
        debug=bool(data.get("debug", True)),
        library_dir=_resolve_project_path(
            str(data.get("library_dir", "biblioteca"))
        ),
        schema_file=_resolve_project_path(
            str(
                data.get(
                    "schema_file",
                    "schemas/apostila-subject.schema.json",
                )
            )
        ),
        prompt_template_file=_resolve_project_path(
            str(
                data.get(
                    "prompt_template_file",
                    "prompts/converter-apostila-para-json.txt",
                )
            )
        ),
        projects_dir=_resolve_project_path(
            str(data.get("projects_dir", "projetos"))
        ),
        uploads_dir=_resolve_project_path(
            str(data.get("uploads_dir", "uploads"))
        ),
        temp_dir=_resolve_project_path(
            str(data.get("temp_dir", "temp"))
        ),
        output_dir=_resolve_project_path(
            str(data.get("output_dir", "output"))
        ),
        editor=EditorSettings(
            nome=str(
                editor_data.get(
                    "nome",
                    "Fácil Digital Mais",
                )
            ),
            site=str(
                editor_data.get(
                    "site",
                    "facildigitalmais.com",
                )
            ),
        ),
    )