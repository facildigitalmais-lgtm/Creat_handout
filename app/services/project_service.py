from __future__ import annotations

import json
import re
import shutil
import unicodedata
import uuid
import warnings

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, BinaryIO

from PIL import Image, UnidentifiedImageError

from app.core.settings import get_settings
from app.models.project import ProjectPayload
from app.services.subject_catalog import SubjectCatalogService


PROJECT_ID_PATTERN = re.compile(
    r"^[a-f0-9]{12}$"
)

MAX_COVER_SIZE_BYTES = (
    30 * 1024 * 1024
)

MAX_COVER_PIXELS = 80_000_000

ALLOWED_IMAGE_FORMATS = {
    "PNG": {
        "extension": ".png",
        "mime_type": "image/png",
    },
    "JPEG": {
        "extension": ".jpg",
        "mime_type": "image/jpeg",
    },
    "WEBP": {
        "extension": ".webp",
        "mime_type": "image/webp",
    },
}


class ProjectError(Exception):
    pass


class ProjectNotFoundError(
    ProjectError
):
    pass


class ProjectValidationError(
    ProjectError
):
    pass


class CoverValidationError(
    ProjectError
):
    pass


class ProjectService:
    def __init__(self) -> None:
        settings = get_settings()

        self.projects_dir = (
            settings.projects_dir
        )

        self.projects_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = RLock()

    def list_projects(
        self,
    ) -> dict[str, Any]:
        projects: list[
            dict[str, Any]
        ] = []

        invalid_projects: list[
            dict[str, Any]
        ] = []

        for directory in sorted(
            self.projects_dir.iterdir(),
            key=lambda path: (
                path.name.casefold()
            ),
        ):
            if not directory.is_dir():
                continue

            project_file = (
                directory / "project.json"
            )

            if not project_file.exists():
                continue

            try:
                project = (
                    self._read_project_file(
                        project_file
                    )
                )

                projects.append(
                    self._project_summary(
                        project
                    )
                )

            except Exception as error:
                invalid_projects.append(
                    {
                        "pasta": (
                            directory.name
                        ),
                        "erro": str(error),
                    }
                )

        projects.sort(
            key=lambda item: (
                item.get(
                    "updated_at"
                )
                or ""
            ),
            reverse=True,
        )

        return {
            "projetos": projects,
            "invalidos": invalid_projects,
            "total": len(projects),
        }

    def get_project(
        self,
        project_id: str,
        catalog: (
            SubjectCatalogService
            | None
        ) = None,
    ) -> dict[str, Any]:
        directory = (
            self._find_project_directory(
                project_id
            )
        )

        project = (
            self._read_project_file(
                directory
                / "project.json"
            )
        )

        result = dict(project)

        cover = project.get("capa")

        if isinstance(
            cover,
            dict,
        ) and cover.get("arquivo"):
            result["cover_url"] = (
                "/api/projetos/"
                f"{project_id}/capa"
            )
        else:
            result["cover_url"] = None

        if catalog is not None:
            result["integridade"] = (
                self._check_subject_integrity(
                    project=project,
                    catalog=catalog,
                )
            )

        return result

    def save_project(
        self,
        payload: ProjectPayload,
        catalog: SubjectCatalogService,
    ) -> dict[str, Any]:
        title = (
            payload.dados.titulo.strip()
        )

        if not title:
            raise ProjectValidationError(
                "O nome da apostila "
                "não pode ficar vazio."
            )

        resolved_subjects = (
            self._resolve_subjects(
                payload=payload,
                catalog=catalog,
            )
        )

        with self._lock:
            existing_project: (
                dict[str, Any]
                | None
            ) = None

            current_directory: (
                Path
                | None
            ) = None

            if payload.project_id:
                current_directory = (
                    self._find_project_directory(
                        payload.project_id
                    )
                )

                existing_project = (
                    self._read_project_file(
                        current_directory
                        / "project.json"
                    )
                )

                project_id = (
                    payload.project_id
                )

            else:
                project_id = (
                    uuid.uuid4()
                    .hex[:12]
                )

            slug = self._slugify(
                title
            )

            desired_directory = (
                self.projects_dir
                / f"{slug}__{project_id}"
            )

            if current_directory is None:
                if desired_directory.exists():
                    raise ProjectValidationError(
                        "Já existe uma pasta "
                        "para este projeto."
                    )

                desired_directory.mkdir(
                    parents=True,
                    exist_ok=False,
                )

                project_directory = (
                    desired_directory
                )

            else:
                project_directory = (
                    current_directory
                )

                if (
                    current_directory
                    != desired_directory
                ):
                    if (
                        desired_directory
                        .exists()
                    ):
                        raise (
                            ProjectValidationError(
                                "Não foi possível "
                                "renomear a pasta "
                                "do projeto porque "
                                "o destino já existe."
                            )
                        )

                    current_directory.rename(
                        desired_directory
                    )

                    project_directory = (
                        desired_directory
                    )

            now = self._now()

            created_at = now

            existing_cover = None
            existing_pdf_preview = None

            if existing_project:
                created_at = (
                    existing_project.get(
                        "created_at"
                    )
                    or now
                )

                existing_cover = (
                    existing_project.get(
                        "capa"
                    )
                )

                existing_pdf_preview = (
                    existing_project.get(
                        "pdf_preview"
                    )
                )

                if isinstance(
                    existing_pdf_preview,
                    dict,
                ):
                    existing_pdf_preview = dict(
                        existing_pdf_preview
                    )

                    existing_pdf_preview[
                        "stale"
                    ] = True

            project = {
                "schema_version": "1.0",
                "document_type": (
                    "apostila_project"
                ),
                "project_id": project_id,
                "slug": slug,
                "created_at": created_at,
                "updated_at": now,
                "dados": (
                    payload.dados.model_dump(
                        mode="json"
                    )
                ),
                "materias": (
                    resolved_subjects
                ),
                "editorial": (
                    payload.editorial
                    .model_dump(
                        mode="json"
                    )
                ),
                "capa": existing_cover,
                "pdf_preview": (
                    existing_pdf_preview
                ),
            }

            self._write_project(
                project_directory,
                project,
            )

        return self.get_project(
            project_id,
            catalog,
        )

    def delete_project(
        self,
        project_id: str,
    ) -> None:
        with self._lock:
            directory = (
                self._find_project_directory(
                    project_id
                )
            )

            shutil.rmtree(
                directory
            )

    def save_cover(
        self,
        *,
        project_id: str,
        file_obj: BinaryIO,
        filename: str | None,
        content_type: str | None,
    ) -> dict[str, Any]:
        del content_type

        with self._lock:
            directory = (
                self._find_project_directory(
                    project_id
                )
            )

            project_file = (
                directory / "project.json"
            )

            project = (
                self._read_project_file(
                    project_file
                )
            )

            image_info = (
                self._validate_cover_file(
                    file_obj
                )
            )

            format_name = (
                image_info["format"]
            )

            format_config = (
                ALLOWED_IMAGE_FORMATS[
                    format_name
                ]
            )

            extension = (
                format_config[
                    "extension"
                ]
            )

            final_filename = (
                f"capa{extension}"
            )

            final_path = (
                directory
                / final_filename
            )

            temp_path = (
                directory
                / (
                    ".cover-upload-"
                    f"{uuid.uuid4().hex}.tmp"
                )
            )

            file_obj.seek(0)

            try:
                with temp_path.open(
                    "wb"
                ) as destination:
                    shutil.copyfileobj(
                        file_obj,
                        destination,
                    )

                temp_path.replace(
                    final_path
                )

            finally:
                if temp_path.exists():
                    temp_path.unlink(
                        missing_ok=True
                    )

            for old_cover in (
                directory.glob(
                    "capa.*"
                )
            ):
                if (
                    old_cover
                    != final_path
                    and old_cover.is_file()
                ):
                    old_cover.unlink(
                        missing_ok=True
                    )

            project["capa"] = {
                "arquivo": (
                    final_filename
                ),
                "nome_original": (
                    Path(
                        filename
                        or final_filename
                    ).name
                ),
                "mime_type": (
                    format_config[
                        "mime_type"
                    ]
                ),
                "formato": format_name,
                "tamanho_bytes": (
                    image_info[
                        "size_bytes"
                    ]
                ),
                "largura_px": (
                    image_info[
                        "width"
                    ]
                ),
                "altura_px": (
                    image_info[
                        "height"
                    ]
                ),
            }

            project["updated_at"] = (
                self._now()
            )

            self._mark_pdf_stale(
                project
            )

            self._write_project(
                directory,
                project,
            )

        return self.get_project(
            project_id
        )

    def delete_cover(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            directory = (
                self._find_project_directory(
                    project_id
                )
            )

            project = (
                self._read_project_file(
                    directory
                    / "project.json"
                )
            )

            for cover_path in (
                directory.glob(
                    "capa.*"
                )
            ):
                if cover_path.is_file():
                    cover_path.unlink(
                        missing_ok=True
                    )

            project["capa"] = None

            project["updated_at"] = (
                self._now()
            )

            self._mark_pdf_stale(
                project
            )

            self._write_project(
                directory,
                project,
            )

        return self.get_project(
            project_id
        )

    def get_cover_file(
        self,
        project_id: str,
    ) -> tuple[Path, str]:
        directory = (
            self._find_project_directory(
                project_id
            )
        )

        project = (
            self._read_project_file(
                directory
                / "project.json"
            )
        )

        cover = project.get("capa")

        if not isinstance(
            cover,
            dict,
        ):
            raise ProjectNotFoundError(
                "O projeto não possui capa."
            )

        filename = cover.get(
            "arquivo"
        )

        mime_type = cover.get(
            "mime_type"
        )

        if (
            not isinstance(
                filename,
                str,
            )
            or not filename
        ):
            raise ProjectNotFoundError(
                "A capa do projeto "
                "não foi encontrada."
            )

        cover_path = (
            directory / filename
        )

        if not cover_path.exists():
            raise ProjectNotFoundError(
                "O arquivo físico da capa "
                "não foi encontrado."
            )

        return (
            cover_path,
            (
                str(mime_type)
                if mime_type
                else "application/octet-stream"
            ),
        )

    def get_project_directory(
        self,
        project_id: str,
    ) -> Path:
        """
        Retorna a pasta física do projeto.

        O caminho só é retornado depois que
        project_id passa pela validação interna.
        """

        return self._find_project_directory(
            project_id
        )

    def update_pdf_preview_metadata(
        self,
        project_id: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Atualiza os metadados do PDF de revisão
        depois de uma geração bem-sucedida.
        """

        with self._lock:
            directory = (
                self._find_project_directory(
                    project_id
                )
            )

            project = (
                self._read_project_file(
                    directory
                    / "project.json"
                )
            )

            project[
                "pdf_preview"
            ] = dict(
                metadata
            )

            project[
                "updated_at"
            ] = self._now()

            self._write_project(
                directory,
                project,
            )

        return self.get_project(
            project_id
        )

    def get_preview_pdf_file(
        self,
        project_id: str,
    ) -> tuple[Path, dict[str, Any]]:
        """
        Localiza o PDF de revisão gerado.
        """

        directory = (
            self._find_project_directory(
                project_id
            )
        )

        project = (
            self._read_project_file(
                directory
                / "project.json"
            )
        )

        metadata = project.get(
            "pdf_preview"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            raise ProjectNotFoundError(
                "O projeto ainda não possui "
                "uma prévia PDF gerada."
            )

        filename = metadata.get(
            "arquivo"
        )

        if not isinstance(
            filename,
            str,
        ) or not filename:
            raise ProjectNotFoundError(
                "Os metadados do PDF "
                "não possuem arquivo válido."
            )

        safe_filename = Path(
            filename
        ).name

        if safe_filename != filename:
            raise ProjectValidationError(
                "Nome de arquivo PDF inválido."
            )

        path = (
            directory
            / safe_filename
        )

        if not path.exists():
            raise ProjectNotFoundError(
                "O arquivo PDF de revisão "
                "não foi encontrado."
            )

        return (
            path,
            dict(metadata),
        )

    def _resolve_subjects(
        self,
        *,
        payload: ProjectPayload,
        catalog: SubjectCatalogService,
    ) -> list[dict[str, Any]]:
        seen_ids: set[str] = set()

        resolved: list[
            dict[str, Any]
        ] = []

        ordered_subjects = sorted(
            payload.materias,
            key=lambda item: (
                item.ordem
            ),
        )

        for index, item in enumerate(
            ordered_subjects,
            start=1,
        ):
            if (
                item.id_materia
                in seen_ids
            ):
                raise (
                    ProjectValidationError(
                        "Uma matéria aparece "
                        "mais de uma vez no projeto: "
                        f"{item.id_materia}"
                    )
                )

            seen_ids.add(
                item.id_materia
            )

            metadata = (
                catalog
                .get_subject_metadata(
                    item.id_materia
                )
            )

            if metadata is None:
                raise (
                    ProjectValidationError(
                        "Matéria não encontrada "
                        "na biblioteca: "
                        f"{item.id_materia}"
                    )
                )

            if not metadata.get(
                "valido"
            ):
                raise (
                    ProjectValidationError(
                        "A matéria "
                        f"{metadata.get('materia')!r} "
                        "possui erros de validação "
                        "e não pode ser adicionada."
                    )
                )

            resolved.append(
                {
                    "id_materia": (
                        item.id_materia
                    ),
                    "ordem": index,
                    "materia": (
                        metadata.get(
                            "materia"
                        )
                    ),
                    "codigo_materia": (
                        metadata.get(
                            "codigo_materia"
                        )
                    ),
                    "arquivo": (
                        metadata.get(
                            "arquivo"
                        )
                    ),
                    "schema_version": (
                        metadata.get(
                            "schema_version"
                        )
                    ),
                }
            )

        return resolved

    def _check_subject_integrity(
        self,
        *,
        project: dict[str, Any],
        catalog: SubjectCatalogService,
    ) -> dict[str, Any]:
        missing: list[
            dict[str, Any]
        ] = []

        invalid: list[
            dict[str, Any]
        ] = []

        subjects = project.get(
            "materias"
        )

        if not isinstance(
            subjects,
            list,
        ):
            subjects = []

        for subject in subjects:
            if not isinstance(
                subject,
                dict,
            ):
                continue

            subject_id = subject.get(
                "id_materia"
            )

            if not isinstance(
                subject_id,
                str,
            ):
                continue

            metadata = (
                catalog
                .get_subject_metadata(
                    subject_id
                )
            )

            if metadata is None:
                missing.append(
                    {
                        "id_materia": (
                            subject_id
                        ),
                        "materia": (
                            subject.get(
                                "materia"
                            )
                        ),
                    }
                )

                continue

            if not metadata.get(
                "valido"
            ):
                invalid.append(
                    {
                        "id_materia": (
                            subject_id
                        ),
                        "materia": (
                            metadata.get(
                                "materia"
                            )
                        ),
                    }
                )

        return {
            "ok": (
                not missing
                and not invalid
            ),
            "materias_ausentes": (
                missing
            ),
            "materias_invalidas": (
                invalid
            ),
        }

    def _validate_cover_file(
        self,
        file_obj: BinaryIO,
    ) -> dict[str, Any]:
        try:
            file_obj.seek(
                0,
                2,
            )

            size_bytes = (
                file_obj.tell()
            )

            file_obj.seek(0)

        except Exception as error:
            raise CoverValidationError(
                "Não foi possível "
                "ler o arquivo da capa."
            ) from error

        if size_bytes <= 0:
            raise CoverValidationError(
                "O arquivo da capa "
                "está vazio."
            )

        if (
            size_bytes
            > MAX_COVER_SIZE_BYTES
        ):
            raise CoverValidationError(
                "A capa excede o limite "
                "de 30 MB."
            )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    Image.DecompressionBombWarning,
                )

                image = Image.open(
                    file_obj
                )

                format_name = (
                    image.format
                )

                image.verify()

            file_obj.seek(0)

            image = Image.open(
                file_obj
            )

            width, height = (
                image.size
            )

        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombWarning,
        ) as error:
            raise CoverValidationError(
                "O arquivo enviado não "
                "é uma imagem válida."
            ) from error

        finally:
            file_obj.seek(0)

        if (
            format_name
            not in ALLOWED_IMAGE_FORMATS
        ):
            raise CoverValidationError(
                "Formato de imagem "
                "não suportado. "
                "Use PNG, JPEG ou WEBP."
            )

        if (
            width <= 0
            or height <= 0
        ):
            raise CoverValidationError(
                "A imagem possui "
                "dimensões inválidas."
            )

        if (
            width * height
            > MAX_COVER_PIXELS
        ):
            raise CoverValidationError(
                "A imagem possui "
                "resolução excessivamente "
                "alta para processamento."
            )

        return {
            "format": format_name,
            "width": width,
            "height": height,
            "size_bytes": size_bytes,
        }

    def _project_summary(
        self,
        project: dict[str, Any],
    ) -> dict[str, Any]:
        project_id = project.get(
            "project_id"
        )

        dados = project.get(
            "dados"
        )

        if not isinstance(
            dados,
            dict,
        ):
            dados = {}

        subjects = project.get(
            "materias"
        )

        if not isinstance(
            subjects,
            list,
        ):
            subjects = []

        cover = project.get(
            "capa"
        )

        has_cover = isinstance(
            cover,
            dict,
        )

        pdf_preview = project.get(
            "pdf_preview"
        )

        has_pdf = (
            isinstance(
                pdf_preview,
                dict,
            )
            and bool(
                pdf_preview.get(
                    "arquivo"
                )
            )
        )

        return {
            "project_id": project_id,
            "slug": project.get(
                "slug"
            ),
            "titulo": dados.get(
                "titulo"
            ),
            "concurso": dados.get(
                "concurso"
            ),
            "cargo": dados.get(
                "cargo"
            ),
            "banca": dados.get(
                "banca"
            ),
            "ano": dados.get(
                "ano"
            ),
            "created_at": (
                project.get(
                    "created_at"
                )
            ),
            "updated_at": (
                project.get(
                    "updated_at"
                )
            ),
            "total_materias": len(
                subjects
            ),
            "tem_capa": has_cover,
            "cover_url": (
                (
                    "/api/projetos/"
                    f"{project_id}/capa"
                )
                if has_cover
                else None
            ),
            "tem_pdf": has_pdf,
            "pdf_stale": (
                bool(
                    pdf_preview.get(
                        "stale",
                        False,
                    )
                )
                if isinstance(
                    pdf_preview,
                    dict,
                )
                else False
            ),
            "pdf_paginas": (
                pdf_preview.get(
                    "paginas"
                )
                if isinstance(
                    pdf_preview,
                    dict,
                )
                else None
            ),
        }

    def _find_project_directory(
        self,
        project_id: str,
    ) -> Path:
        self._validate_project_id(
            project_id
        )

        matches = [
            path
            for path in (
                self.projects_dir.glob(
                    f"*__{project_id}"
                )
            )
            if path.is_dir()
        ]

        if not matches:
            raise ProjectNotFoundError(
                "Projeto não encontrado."
            )

        if len(matches) > 1:
            raise ProjectValidationError(
                "Existem múltiplas pastas "
                "para o mesmo projeto."
            )

        return matches[0]

    @staticmethod
    def _read_project_file(
        project_file: Path,
    ) -> dict[str, Any]:
        if not project_file.exists():
            raise ProjectNotFoundError(
                "Arquivo project.json "
                "não encontrado."
            )

        try:
            with project_file.open(
                "r",
                encoding="utf-8",
            ) as file:
                project = json.load(
                    file
                )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise ProjectValidationError(
                "O arquivo project.json "
                "não pôde ser lido."
            ) from error

        if not isinstance(
            project,
            dict,
        ):
            raise ProjectValidationError(
                "O project.json deve "
                "conter um objeto JSON."
            )

        if (
            project.get(
                "document_type"
            )
            != "apostila_project"
        ):
            raise ProjectValidationError(
                "Tipo de documento "
                "de projeto inválido."
            )

        return project

    @staticmethod
    def _write_project(
        directory: Path,
        project: dict[str, Any],
    ) -> None:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        project_file = (
            directory / "project.json"
        )

        temp_file = (
            directory
            / ".project.json.tmp"
        )

        serialized = json.dumps(
            project,
            ensure_ascii=False,
            indent=2,
        )

        temp_file.write_text(
            serialized + "\n",
            encoding="utf-8",
        )

        temp_file.replace(
            project_file
        )

    @staticmethod
    def _mark_pdf_stale(
        project: dict[str, Any],
    ) -> None:
        metadata = project.get(
            "pdf_preview"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            return

        metadata = dict(
            metadata
        )

        metadata[
            "stale"
        ] = True

        project[
            "pdf_preview"
        ] = metadata

    @staticmethod
    def _validate_project_id(
        project_id: str,
    ) -> None:
        if not PROJECT_ID_PATTERN.fullmatch(
            project_id
        ):
            raise ProjectValidationError(
                "Identificador de projeto "
                "inválido."
            )

    @staticmethod
    def _slugify(
        value: str,
    ) -> str:
        normalized = (
            unicodedata.normalize(
                "NFKD",
                value,
            )
            .encode(
                "ascii",
                "ignore",
            )
            .decode(
                "ascii"
            )
            .lower()
        )

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            normalized,
        )

        normalized = (
            normalized
            .strip("-")
        )

        if not normalized:
            normalized = "apostila"

        return normalized[:90]

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()


project_service = ProjectService()