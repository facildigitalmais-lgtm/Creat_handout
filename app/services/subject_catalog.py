from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.settings import get_settings
from app.validators.subject_validator import SubjectValidator


CODE_FILENAME_PATTERN = re.compile(
    r"^(?P<codigo>\d{3,})[_-](?P<materia>.+)$",
    re.IGNORECASE,
)


class SubjectCatalogService:
    """
    Gerencia a biblioteca de matérias completas.

    Regra fundamental:

        1 arquivo JSON = 1 matéria completa.

    O serviço:

    - descobre arquivos JSON;
    - valida cada matéria;
    - extrai metadados;
    - detecta conflitos;
    - fornece catálogo leve para a interface;
    - carrega o documento integral apenas quando necessário.
    """

    def __init__(self) -> None:
        settings = get_settings()

        self.library_dir = settings.library_dir

        self.validator = SubjectValidator(
            settings.schema_file
        )

        self._lock = RLock()

        self._subjects: list[
            dict[str, Any]
        ] = []

        self._loaded_at: str | None = None

    def reload(self) -> dict[str, Any]:
        """
        Relê integralmente a biblioteca.
        """

        subjects: list[
            dict[str, Any]
        ] = []

        self.library_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for file_path in self._discover_json_files():
            metadata = self._load_subject_metadata(
                file_path
            )

            subjects.append(
                metadata
            )

        self._apply_catalog_conflicts(
            subjects
        )

        subjects.sort(
            key=self._sort_key
        )

        loaded_at = datetime.now(
            timezone.utc
        ).isoformat()

        with self._lock:
            self._subjects = subjects
            self._loaded_at = loaded_at

        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        """
        Retorna uma cópia segura do catálogo atual.
        """

        with self._lock:
            subjects = deepcopy(
                self._subjects
            )

            loaded_at = self._loaded_at

        valid_count = sum(
            1
            for subject in subjects
            if subject.get("valido")
        )

        invalid_count = (
            len(subjects)
            - valid_count
        )

        return {
            "carregado_em": loaded_at,
            "estatisticas": {
                "arquivos": len(subjects),
                "validos": valid_count,
                "invalidos": invalid_count,
                "materias": len(subjects),
            },
            "materias": subjects,
        }

    def list_subjects(
        self,
    ) -> list[dict[str, Any]]:
        """
        Lista as matérias disponíveis.
        """

        snapshot = self.snapshot()

        return snapshot[
            "materias"
        ]

    def get_subject_metadata(
        self,
        subject_id: str,
    ) -> dict[str, Any] | None:
        """
        Retorna os metadados de uma matéria pelo ID.
        """

        with self._lock:
            for subject in self._subjects:
                if (
                    subject.get(
                        "id_materia"
                    )
                    == subject_id
                ):
                    return deepcopy(
                        subject
                    )

        return None

    def get_subject_document(
        self,
        subject_id: str,
    ) -> dict[str, Any]:
        """
        Carrega o JSON integral de uma matéria.

        O catálogo mantém apenas metadados em memória;
        o conteúdo completo é lido quando necessário.
        """

        metadata = (
            self.get_subject_metadata(
                subject_id
            )
        )

        if metadata is None:
            raise KeyError(
                "Matéria não encontrada: "
                f"{subject_id}"
            )

        relative_file = metadata.get(
            "arquivo"
        )

        if not isinstance(
            relative_file,
            str,
        ):
            raise ValueError(
                "A matéria não possui "
                "caminho de arquivo válido."
            )

        file_path = (
            self.library_dir
            / relative_file
        )

        if not file_path.exists():
            raise FileNotFoundError(
                "Arquivo da matéria "
                f"não encontrado: {file_path}"
            )

        with file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            document = json.load(
                file
            )

        if not isinstance(
            document,
            dict,
        ):
            raise ValueError(
                "O documento da matéria "
                "não possui um objeto JSON "
                "na raiz."
            )

        return document

    def grouped(
        self,
    ) -> list[dict[str, Any]]:
        """
        Compatibilidade temporária com a
        interface antiga.

        Cada grupo representa agora uma única
        matéria completa.
        """

        groups: list[
            dict[str, Any]
        ] = []

        for subject in self.list_subjects():
            legacy_item = {
                **subject,
                "assunto": subject.get(
                    "materia"
                ),
                "total_secoes": (
                    subject.get(
                        "total_secoes"
                    )
                    or 0
                ),
                "total_blocos": (
                    subject.get(
                        "total_blocos"
                    )
                    or 0
                ),
                "total_exercicios": (
                    subject.get(
                        "total_exercicios"
                    )
                    or 0
                ),
            }

            groups.append(
                {
                    "materia": (
                        subject.get(
                            "materia"
                        )
                        or
                        "Matéria não identificada"
                    ),
                    "codigo_materia": (
                        subject.get(
                            "codigo_materia"
                        )
                    ),
                    "modulos": [
                        legacy_item
                    ],
                    "validos": (
                        1
                        if subject.get(
                            "valido"
                        )
                        else 0
                    ),
                    "invalidos": (
                        0
                        if subject.get(
                            "valido"
                        )
                        else 1
                    ),
                }
            )

        return groups

    def _discover_json_files(
        self,
    ) -> list[Path]:
        """
        Descobre matérias JSON recursivamente.

        Diretórios iniciados por "_" são ignorados.
        """

        files: list[
            Path
        ] = []

        for file_path in (
            self.library_dir.rglob(
                "*.json"
            )
        ):
            if not file_path.is_file():
                continue

            relative_path = (
                file_path.relative_to(
                    self.library_dir
                )
            )

            parent_parts = (
                relative_path.parts[:-1]
            )

            if any(
                part.startswith("_")
                for part in parent_parts
            ):
                continue

            files.append(
                file_path
            )

        files.sort(
            key=lambda path: (
                str(path).casefold()
            )
        )

        return files

    def _load_subject_metadata(
        self,
        file_path: Path,
    ) -> dict[str, Any]:
        """
        Lê um JSON de matéria, valida-o e
        produz somente os metadados necessários
        ao catálogo.
        """

        relative_path = (
            file_path.relative_to(
                self.library_dir
            )
        )

        result: dict[str, Any] = {
            "arquivo": (
                relative_path.as_posix()
            ),
            "nome_arquivo": (
                file_path.name
            ),
            "valido": False,
            "erros": [],
            "id_materia": None,
            "codigo_materia": None,
            "materia": None,
            "titulo": None,
            "descricao": None,
            "nivel": None,
            "schema_version": None,
            "document_type": None,
            "versao_conteudo": None,
            "perfil_epistemologico": [],
            "total_topicos": 0,
            "total_secoes": 0,
            "total_blocos": 0,
            "total_exercicios": 0,
            "total_gabaritos": 0,
            "total_referencias": 0,
            "total_fontes": 0,
            "total_assets": 0,
            "topicos": [],
            "possui_alertas": False,
            "total_alertas": 0,
        }

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                document = json.load(
                    file
                )

        except json.JSONDecodeError as error:
            result["erros"] = [
                (
                    "JSON inválido: "
                    f"linha {error.lineno}, "
                    f"coluna {error.colno}: "
                    f"{error.msg}"
                )
            ]

            return result

        except OSError as error:
            result["erros"] = [
                (
                    "Não foi possível "
                    "ler o arquivo: "
                    f"{error}"
                )
            ]

            return result

        if not isinstance(
            document,
            dict,
        ):
            result["erros"] = [
                (
                    "O conteúdo raiz do JSON "
                    "deve ser um objeto."
                )
            ]

            return result

        cabecalho = document.get(
            "cabecalho"
        )

        if not isinstance(
            cabecalho,
            dict,
        ):
            cabecalho = {}

        filename_metadata = (
            self._parse_filename(
                file_path.stem
            )
        )

        codigo_materia = (
            self._clean_text(
                cabecalho.get(
                    "codigo_materia"
                )
            )
            or
            filename_metadata.get(
                "codigo_materia"
            )
        )

        materia = (
            self._clean_text(
                cabecalho.get(
                    "materia"
                )
            )
            or
            filename_metadata.get(
                "materia"
            )
            or
            self._infer_matter_from_folder(
                file_path
            )
            or
            "Matéria não identificada"
        )

        title = (
            self._clean_text(
                cabecalho.get(
                    "titulo_sugerido"
                )
            )
            or materia
        )

        map_items = (
            self._safe_list(
                document.get(
                    "mapa_estrutura"
                )
            )
        )

        content_items = (
            self._safe_list(
                document.get(
                    "conteudo"
                )
            )
        )

        exercises = (
            self._safe_list(
                document.get(
                    "exercicios"
                )
            )
        )

        answers = (
            self._safe_list(
                document.get(
                    "gabaritos"
                )
            )
        )

        references = (
            self._safe_list(
                document.get(
                    "referencias"
                )
            )
        )

        sources = (
            self._safe_list(
                document.get(
                    "fontes"
                )
            )
        )

        assets = (
            self._safe_list(
                document.get(
                    "assets"
                )
            )
        )

        errors = (
            self.validator.validate(
                document
            )
        )

        blocks_count = 0

        for section in content_items:
            if not isinstance(
                section,
                dict,
            ):
                continue

            blocks = section.get(
                "blocos"
            )

            if isinstance(
                blocks,
                list,
            ):
                blocks_count += len(
                    blocks
                )

        top_level_items = [
            item
            for item in map_items
            if (
                isinstance(
                    item,
                    dict,
                )
                and
                item.get(
                    "parent_id"
                )
                is None
            )
        ]

        top_level_items.sort(
            key=lambda item: (
                self._integer_value(
                    item.get(
                        "ordem"
                    )
                ),
                str(
                    item.get(
                        "titulo"
                    )
                    or ""
                ).casefold(),
            )
        )

        topic_titles = [
            str(
                item.get(
                    "titulo"
                )
                or ""
            ).strip()
            for item in top_level_items
            if str(
                item.get(
                    "titulo"
                )
                or ""
            ).strip()
        ]

        profile = (
            cabecalho.get(
                "perfil_epistemologico"
            )
        )

        if not isinstance(
            profile,
            list,
        ):
            profile = []

        auditoria = document.get(
            "auditoria"
        )

        if not isinstance(
            auditoria,
            dict,
        ):
            auditoria = {}

        alerts = self._safe_list(
            auditoria.get(
                "alertas"
            )
        )

        result.update(
            {
                "valido": (
                    not errors
                ),
                "erros": errors,
                "id_materia": (
                    self._clean_text(
                        cabecalho.get(
                            "id_materia"
                        )
                    )
                ),
                "codigo_materia": (
                    codigo_materia
                ),
                "materia": materia,
                "titulo": title,
                "descricao": (
                    self._clean_text(
                        cabecalho.get(
                            "descricao"
                        )
                    )
                ),
                "nivel": (
                    self._clean_text(
                        cabecalho.get(
                            "nivel"
                        )
                    )
                ),
                "schema_version": (
                    document.get(
                        "schema_version"
                    )
                ),
                "document_type": (
                    document.get(
                        "document_type"
                    )
                ),
                "versao_conteudo": (
                    self._clean_text(
                        cabecalho.get(
                            "versao_conteudo"
                        )
                    )
                ),
                "perfil_epistemologico": (
                    profile
                ),
                "total_topicos": len(
                    top_level_items
                ),
                "total_secoes": len(
                    map_items
                ),
                "total_blocos": (
                    blocks_count
                ),
                "total_exercicios": len(
                    exercises
                ),
                "total_gabaritos": len(
                    answers
                ),
                "total_referencias": len(
                    references
                ),
                "total_fontes": len(
                    sources
                ),
                "total_assets": len(
                    assets
                ),
                "topicos": (
                    topic_titles
                ),
                "possui_alertas": (
                    bool(alerts)
                ),
                "total_alertas": len(
                    alerts
                ),
            }
        )

        return result

    def _apply_catalog_conflicts(
        self,
        subjects: list[
            dict[str, Any]
        ],
    ) -> None:
        """
        Detecta IDs e códigos incompatíveis
        duplicados na biblioteca.
        """

        by_id: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        by_code: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for subject in subjects:
            subject_id = subject.get(
                "id_materia"
            )

            code = subject.get(
                "codigo_materia"
            )

            if (
                isinstance(
                    subject_id,
                    str,
                )
                and subject_id
            ):
                by_id.setdefault(
                    subject_id,
                    [],
                ).append(
                    subject
                )

            if (
                isinstance(
                    code,
                    str,
                )
                and code
            ):
                by_code.setdefault(
                    code,
                    [],
                ).append(
                    subject
                )

        for (
            subject_id,
            matches,
        ) in by_id.items():
            if len(matches) <= 1:
                continue

            for subject in matches:
                self._append_error(
                    subject,
                    (
                        "ID de matéria "
                        "duplicado na biblioteca: "
                        f"{subject_id!r}"
                    ),
                )

        for (
            code,
            matches,
        ) in by_code.items():
            if len(matches) <= 1:
                continue

            unique_subject_ids = {
                item.get(
                    "id_materia"
                )
                for item in matches
            }

            if len(
                unique_subject_ids
            ) <= 1:
                continue

            for subject in matches:
                self._append_error(
                    subject,
                    (
                        "Código de matéria "
                        "duplicado na biblioteca: "
                        f"{code!r}"
                    ),
                )

    @staticmethod
    def _append_error(
        subject: dict[str, Any],
        message: str,
    ) -> None:
        errors = subject.get(
            "erros"
        )

        if not isinstance(
            errors,
            list,
        ):
            errors = []

            subject[
                "erros"
            ] = errors

        if message not in errors:
            errors.append(
                message
            )

        subject[
            "valido"
        ] = False

    @staticmethod
    def _parse_filename(
        stem: str,
    ) -> dict[
        str,
        str | None,
    ]:
        normalized = (
            stem.strip()
        )

        coded_match = (
            CODE_FILENAME_PATTERN.match(
                normalized
            )
        )

        if coded_match:
            return {
                "codigo_materia": (
                    coded_match.group(
                        "codigo"
                    )
                ),
                "materia": (
                    SubjectCatalogService
                    ._humanize_slug(
                        coded_match.group(
                            "materia"
                        )
                    )
                ),
            }

        return {
            "codigo_materia": None,
            "materia": (
                SubjectCatalogService
                ._humanize_slug(
                    normalized
                )
            ),
        }

    def _infer_matter_from_folder(
        self,
        file_path: Path,
    ) -> str | None:
        relative_path = (
            file_path.relative_to(
                self.library_dir
            )
        )

        if len(
            relative_path.parts
        ) <= 1:
            return None

        parent_name = (
            relative_path.parts[-2]
        )

        if parent_name.startswith(
            "_"
        ):
            return None

        return self._humanize_slug(
            parent_name
        )

    @staticmethod
    def _humanize_slug(
        value: str,
    ) -> str:
        cleaned = (
            value
            .replace(
                "-",
                " ",
            )
            .replace(
                "_",
                " ",
            )
            .strip()
        )

        cleaned = " ".join(
            cleaned.split()
        )

        if not cleaned:
            return ""

        return (
            cleaned[0].upper()
            + cleaned[1:]
        )

    @staticmethod
    def _clean_text(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        text = str(
            value
        ).strip()

        return (
            text
            or None
        )

    @staticmethod
    def _safe_list(
        value: Any,
    ) -> list[Any]:
        if isinstance(
            value,
            list,
        ):
            return value

        return []

    @staticmethod
    def _integer_value(
        value: Any,
    ) -> int:
        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return 999999

    @staticmethod
    def _sort_key(
        item: dict[str, Any],
    ) -> tuple[
        int,
        str,
        str,
    ]:
        code = item.get(
            "codigo_materia"
        )

        try:
            numeric_code = int(
                code
            )

        except (
            TypeError,
            ValueError,
        ):
            numeric_code = 999999

        return (
            numeric_code,
            str(
                item.get(
                    "materia"
                )
                or ""
            ).casefold(),
            str(
                item.get(
                    "arquivo"
                )
                or ""
            ).casefold(),
        )


subject_catalog_service = (
    SubjectCatalogService()
)