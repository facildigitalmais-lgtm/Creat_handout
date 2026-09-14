from __future__ import annotations

import hashlib
import json
import re
import shutil
import uuid

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Callable

import pypdfium2 as pdfium

from PIL import Image

from app.services.project_service import (
    ProjectNotFoundError,
    ProjectValidationError,
    project_service,
)


AUDIT_DIRNAME = "audit"
AUDIT_FILENAME = "audit.json"

THUMBNAIL_SCALE = 0.72
THUMBNAIL_QUALITY = 78

A4_WIDTH_POINTS = 595.28
A4_HEIGHT_POINTS = 841.89
PAGE_SIZE_TOLERANCE = 3.0

WHITE_THRESHOLD = 245

BLANK_TEXT_LIMIT = 8
BLANK_INK_RATIO = 0.0015

SPARSE_TEXT_LIMIT = 120
SPARSE_INK_RATIO = 0.018

DENSE_TEXT_LIMIT = 5500
DENSE_INK_RATIO = 0.33

EDGE_MARGIN_PIXELS = 3

LONG_TOKEN_LIMIT = 120

STRUCTURAL_KEYWORDS = (
    "SUMÁRIO",
    "APOSTILA DE ESTUDO",
    "APOSTILA PREPARATÓRIA",
    "APOSTILA PREPARATÓRIA",
    "PARTE ",
    "EXERCÍCIOS",
    "GABARITO COMENTADO",
    "REFERÊNCIAS",
    "BONS ESTUDOS",
    "SOBRE ESTE MATERIAL",
)


class PDFAuditError(
    RuntimeError
):
    pass


class PDFAuditService:
    """
    Auditoria estrutural e visual do PDF gerado.

    A auditoria NÃO substitui inspeção humana final.

    Ela serve como uma primeira barreira automática
    para localizar páginas que merecem atenção antes
    da liberação comercial da apostila.
    """

    def __init__(self) -> None:
        self._lock = RLock()

    def audit_preview(
        self,
        project_id: str,
        progress_callback: (
            Callable[
                [int, str],
                None,
            ]
            | None
        ) = None,
    ) -> dict[str, Any]:
        with self._lock:
            pdf_path, pdf_metadata = (
                project_service
                .get_preview_pdf_file(
                    project_id
                )
            )

            if bool(
                pdf_metadata.get(
                    "stale",
                    False,
                )
            ):
                raise PDFAuditError(
                    "O PDF está desatualizado em relação "
                    "ao projeto. Gere novamente o PDF "
                    "antes de executar a auditoria."
                )

            project_directory = (
                project_service
                .get_project_directory(
                    project_id
                )
            )

            audit_directory = (
                project_directory
                / AUDIT_DIRNAME
            )

            temporary_directory = (
                project_directory
                / (
                    ".audit-"
                    f"{uuid.uuid4().hex}"
                )
            )

            temporary_directory.mkdir(
                parents=True,
                exist_ok=False,
            )

            try:
                result = self._inspect_pdf(
                    project_id=project_id,
                    pdf_path=pdf_path,
                    pdf_metadata=pdf_metadata,
                    output_directory=(
                        temporary_directory
                    ),
                    progress_callback=(
                        progress_callback
                    ),
                )

                audit_file = (
                    temporary_directory
                    / AUDIT_FILENAME
                )

                audit_file.write_text(
                    json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                if audit_directory.exists():
                    shutil.rmtree(
                        audit_directory
                    )

                temporary_directory.rename(
                    audit_directory
                )

            except Exception:
                if (
                    temporary_directory
                    .exists()
                ):
                    shutil.rmtree(
                        temporary_directory,
                        ignore_errors=True,
                    )

                raise

            return result

    def get_audit(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        project_directory = (
            project_service
            .get_project_directory(
                project_id
            )
        )

        audit_file = (
            project_directory
            / AUDIT_DIRNAME
            / AUDIT_FILENAME
        )

        if not audit_file.exists():
            raise ProjectNotFoundError(
                "A auditoria visual ainda "
                "não foi executada."
            )

        try:
            audit = json.loads(
                audit_file.read_text(
                    encoding="utf-8"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
        ) as error:
            raise PDFAuditError(
                "O arquivo da auditoria "
                "não pôde ser lido."
            ) from error

        if not isinstance(
            audit,
            dict,
        ):
            raise PDFAuditError(
                "O arquivo da auditoria "
                "possui formato inválido."
            )

        try:
            _, pdf_metadata = (
                project_service
                .get_preview_pdf_file(
                    project_id
                )
            )

        except ProjectNotFoundError:
            audit["stale"] = True

            return audit

        current_sha = str(
            pdf_metadata.get(
                "sha256"
            )
            or ""
        )

        audited_sha = str(
            audit.get(
                "pdf_sha256"
            )
            or ""
        )

        audit["stale"] = (
            bool(
                pdf_metadata.get(
                    "stale",
                    False,
                )
            )
            or
            not current_sha
            or
            current_sha
            != audited_sha
        )

        return audit

    def get_thumbnail(
        self,
        project_id: str,
        page_number: int,
    ) -> Path:
        if page_number <= 0:
            raise ProjectValidationError(
                "Número de página inválido."
            )

        audit = self.get_audit(
            project_id
        )

        total_pages = int(
            audit.get(
                "total_paginas",
                0,
            )
            or 0
        )

        if (
            page_number
            > total_pages
        ):
            raise ProjectNotFoundError(
                "Página inexistente "
                "na auditoria."
            )

        project_directory = (
            project_service
            .get_project_directory(
                project_id
            )
        )

        filename = (
            f"page-{page_number:04d}.jpg"
        )

        path = (
            project_directory
            / AUDIT_DIRNAME
            / filename
        )

        if not path.exists():
            raise ProjectNotFoundError(
                "Miniatura da página "
                "não encontrada."
            )

        return path

    def _inspect_pdf(
        self,
        *,
        project_id: str,
        pdf_path: Path,
        pdf_metadata: dict[str, Any],
        output_directory: Path,
        progress_callback: (
            Callable[
                [int, str],
                None,
            ]
            | None
        ) = None,
    ) -> dict[str, Any]:
        try:
            pdf = pdfium.PdfDocument(
                str(
                    pdf_path
                )
            )

        except Exception as error:
            raise PDFAuditError(
                "O PDF não pôde ser aberto "
                "pelo motor de auditoria."
            ) from error

        pages: list[
            dict[str, Any]
        ] = []

        try:
            total_pages = len(
                pdf
            )

            if total_pages <= 0:
                raise PDFAuditError(
                    "O PDF não possui páginas."
                )

            for page_index in range(
                total_pages
            ):
                page_number = (
                    page_index + 1
                )

                page = pdf[
                    page_index
                ]

                try:
                    page_result = (
                        self._inspect_page(
                            page=page,
                            page_number=(
                                page_number
                            ),
                            total_pages=(
                                total_pages
                            ),
                            output_directory=(
                                output_directory
                            ),
                        )
                    )

                    pages.append(
                        page_result
                    )

                    if (
                        progress_callback
                        is not None
                    ):
                        audit_progress = (
                            85
                            + int(
                                (
                                    page_number
                                    / total_pages
                                )
                                * 14
                            )
                        )

                        progress_callback(
                            min(
                                audit_progress,
                                99,
                            ),
                            (
                                "Auditando página "
                                f"{page_number} "
                                f"de {total_pages}..."
                            ),
                        )

                finally:
                    self._close_if_possible(
                        page
                    )

        finally:
            self._close_if_possible(
                pdf
            )

        if progress_callback is not None:
            progress_callback(
                99,
                "Finalizando relatório "
                "de auditoria...",
            )

        if progress_callback is not None:
            progress_callback(
                99,
                "Finalizando relatório "
                "de auditoria...",
            )

        summary = (
            self._build_summary(
                pages
            )
        )

        generated_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

        return {
            "schema_version": "1.0",
            "document_type": (
                "pdf_visual_audit"
            ),
            "project_id": project_id,
            "gerado_em": generated_at,
            "pdf_arquivo": (
                pdf_path.name
            ),
            "pdf_sha256": (
                pdf_metadata.get(
                    "sha256"
                )
                or self._sha256(
                    pdf_path
                )
            ),
            "total_paginas": len(
                pages
            ),
            "stale": False,
            "resumo": summary,
            "paginas": pages,
        }

    def _inspect_page(
        self,
        *,
        page: Any,
        page_number: int,
        total_pages: int,
        output_directory: Path,
    ) -> dict[str, Any]:
        width, height = (
            page.get_size()
        )

        text = self._extract_text(
            page
        )

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        text_characters = len(
            normalized_text
        )

        bitmap = None

        try:
            bitmap = page.render(
                scale=THUMBNAIL_SCALE,
                rotation=0,
                fill_color=(
                    255,
                    255,
                    255,
                    255,
                ),
                optimize_mode="print",
            )

            image = (
                bitmap
                .to_pil()
                .convert("RGB")
                .copy()
            )

        except Exception as error:
            raise PDFAuditError(
                "Não foi possível renderizar "
                f"a página {page_number}."
            ) from error

        finally:
            if bitmap is not None:
                self._close_if_possible(
                    bitmap
                )

        thumbnail_filename = (
            f"page-{page_number:04d}.jpg"
        )

        thumbnail_path = (
            output_directory
            / thumbnail_filename
        )

        image.save(
            thumbnail_path,
            format="JPEG",
            quality=THUMBNAIL_QUALITY,
            optimize=True,
            progressive=True,
        )

        visual_metrics = (
            self._visual_metrics(
                image
            )
        )

        issues = (
            self._evaluate_page(
                page_number=page_number,
                total_pages=total_pages,
                width=width,
                height=height,
                text=normalized_text,
                text_characters=(
                    text_characters
                ),
                visual_metrics=(
                    visual_metrics
                ),
            )
        )

        status = (
            self._status_from_issues(
                issues
            )
        )

        return {
            "pagina": page_number,
            "status": status,
            "largura_pt": round(
                float(width),
                2,
            ),
            "altura_pt": round(
                float(height),
                2,
            ),
            "caracteres_texto": (
                text_characters
            ),
            "densidade_tinta": round(
                visual_metrics[
                    "ink_ratio"
                ],
                5,
            ),
            "bbox_conteudo": (
                visual_metrics[
                    "bbox"
                ]
            ),
            "miniatura": (
                thumbnail_filename
            ),
            "preview_texto": (
                normalized_text[:220]
            ),
            "problemas": issues,
        }

    def _evaluate_page(
        self,
        *,
        page_number: int,
        total_pages: int,
        width: float,
        height: float,
        text: str,
        text_characters: int,
        visual_metrics: dict[str, Any],
    ) -> list[dict[str, str]]:
        issues: list[
            dict[str, str]
        ] = []

        ink_ratio = float(
            visual_metrics[
                "ink_ratio"
            ]
        )

        bbox = visual_metrics.get(
            "bbox"
        )

        is_a4 = (
            self._is_a4(
                width,
                height,
            )
        )

        if not is_a4:
            issues.append(
                {
                    "codigo": (
                        "PAGE_SIZE_NOT_A4"
                    ),
                    "gravidade": "erro",
                    "mensagem": (
                        "A página não possui "
                        "dimensões compatíveis "
                        "com A4."
                    ),
                }
            )

        blank_page = (
            text_characters
            <= BLANK_TEXT_LIMIT
            and
            ink_ratio
            <= BLANK_INK_RATIO
        )

        if blank_page:
            issues.append(
                {
                    "codigo": (
                        "POSSIBLE_BLANK_PAGE"
                    ),
                    "gravidade": "erro",
                    "mensagem": (
                        "Página aparentemente "
                        "vazia. Verifique se a "
                        "quebra de página é "
                        "intencional."
                    ),
                }
            )

        structural_page = (
            self._looks_structural(
                text
            )
        )

        sparse_page = (
            not blank_page
            and
            text_characters
            < SPARSE_TEXT_LIMIT
            and
            ink_ratio
            < SPARSE_INK_RATIO
        )

        if (
            sparse_page
            and
            not structural_page
        ):
            issues.append(
                {
                    "codigo": (
                        "SPARSE_PAGE"
                    ),
                    "gravidade": "atencao",
                    "mensagem": (
                        "Página com pouco "
                        "conteúdo aparente. "
                        "Pode haver quebra "
                        "editorial inadequada."
                    ),
                }
            )

        if (
            text_characters
            > DENSE_TEXT_LIMIT
        ):
            issues.append(
                {
                    "codigo": (
                        "VERY_DENSE_TEXT"
                    ),
                    "gravidade": "atencao",
                    "mensagem": (
                        "Quantidade de texto "
                        "muito alta nesta página. "
                        "Verifique legibilidade "
                        "e tamanho tipográfico."
                    ),
                }
            )

        if (
            ink_ratio
            > DENSE_INK_RATIO
            and
            text_characters
            > 1200
        ):
            issues.append(
                {
                    "codigo": (
                        "HIGH_VISUAL_DENSITY"
                    ),
                    "gravidade": "atencao",
                    "mensagem": (
                        "A página apresenta "
                        "densidade visual elevada."
                    ),
                }
            )

        if "\ufffd" in text:
            issues.append(
                {
                    "codigo": (
                        "REPLACEMENT_CHARACTER"
                    ),
                    "gravidade": "erro",
                    "mensagem": (
                        "Foi detectado caractere "
                        "de substituição, possível "
                        "sinal de problema de fonte "
                        "ou codificação."
                    ),
                }
            )

        longest_token = (
            self._longest_token(
                text
            )
        )

        if (
            len(
                longest_token
            )
            > LONG_TOKEN_LIMIT
        ):
            issues.append(
                {
                    "codigo": (
                        "LONG_UNBROKEN_TOKEN"
                    ),
                    "gravidade": "atencao",
                    "mensagem": (
                        "Existe uma sequência "
                        "muito longa sem espaços, "
                        "com risco de extrapolar "
                        "a largura disponível."
                    ),
                }
            )

        if (
            bbox is not None
            and
            not self._expected_full_bleed_page(
                page_number=page_number,
                total_pages=total_pages,
                ink_ratio=ink_ratio,
                text=text,
            )
            and
            self._bbox_touches_edge(
                bbox=bbox,
                image_width=int(
                    visual_metrics[
                        "width"
                    ]
                ),
                image_height=int(
                    visual_metrics[
                        "height"
                    ]
                ),
            )
        ):
            issues.append(
                {
                    "codigo": (
                        "CONTENT_NEAR_PHYSICAL_EDGE"
                    ),
                    "gravidade": "atencao",
                    "mensagem": (
                        "Há conteúdo gráfico "
                        "muito próximo da borda "
                        "física da página."
                    ),
                }
            )

        return issues

    def _visual_metrics(
        self,
        image: Image.Image,
    ) -> dict[str, Any]:
        gray = image.convert(
            "L"
        )

        histogram = (
            gray.histogram()
        )

        total_pixels = (
            gray.width
            * gray.height
        )

        ink_pixels = sum(
            histogram[
                :WHITE_THRESHOLD
            ]
        )

        ink_ratio = (
            ink_pixels
            / total_pixels
            if total_pixels
            else 0.0
        )

        mask = gray.point(
            lambda value: (
                255
                if value
                < WHITE_THRESHOLD
                else 0
            )
        )

        raw_bbox = mask.getbbox()

        bbox: (
            list[int]
            | None
        ) = None

        if raw_bbox is not None:
            bbox = [
                int(value)
                for value
                in raw_bbox
            ]

        return {
            "width": gray.width,
            "height": gray.height,
            "ink_ratio": ink_ratio,
            "bbox": bbox,
        }

    def _extract_text(
        self,
        page: Any,
    ) -> str:
        textpage = None

        try:
            textpage = (
                page.get_textpage()
            )

            return (
                textpage
                .get_text_bounded()
                or ""
            )

        except Exception:
            return ""

        finally:
            if textpage is not None:
                self._close_if_possible(
                    textpage
                )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        value = value.replace(
            "\r\n",
            "\n",
        )

        value = value.replace(
            "\r",
            "\n",
        )

        lines = [
            " ".join(
                line.split()
            )
            for line
            in value.split(
                "\n"
            )
        ]

        return "\n".join(
            line
            for line
            in lines
            if line
        ).strip()

    @staticmethod
    def _looks_structural(
        text: str,
    ) -> bool:
        uppercase = (
            text.upper()
        )

        return any(
            keyword in uppercase
            for keyword
            in STRUCTURAL_KEYWORDS
        )

    @staticmethod
    def _expected_full_bleed_page(
        *,
        page_number: int,
        total_pages: int,
        ink_ratio: float,
        text: str,
    ) -> bool:
        del total_pages

        if (
            page_number == 1
            and ink_ratio
            > 0.10
        ):
            return True

        uppercase = (
            text.upper()
        )

        if (
            "BONS ESTUDOS"
            in uppercase
        ):
            return False

        return False

    @staticmethod
    def _bbox_touches_edge(
        *,
        bbox: list[int],
        image_width: int,
        image_height: int,
    ) -> bool:
        left, top, right, bottom = (
            bbox
        )

        return any(
            (
                left
                <= EDGE_MARGIN_PIXELS,
                top
                <= EDGE_MARGIN_PIXELS,
                right
                >= (
                    image_width
                    - EDGE_MARGIN_PIXELS
                ),
                bottom
                >= (
                    image_height
                    - EDGE_MARGIN_PIXELS
                ),
            )
        )

    @staticmethod
    def _longest_token(
        text: str,
    ) -> str:
        tokens = re.findall(
            r"\S+",
            text,
        )

        if not tokens:
            return ""

        return max(
            tokens,
            key=len,
        )

    @staticmethod
    def _is_a4(
        width: float,
        height: float,
    ) -> bool:
        portrait = (
            abs(
                float(width)
                - A4_WIDTH_POINTS
            )
            <= PAGE_SIZE_TOLERANCE
            and
            abs(
                float(height)
                - A4_HEIGHT_POINTS
            )
            <= PAGE_SIZE_TOLERANCE
        )

        landscape = (
            abs(
                float(width)
                - A4_HEIGHT_POINTS
            )
            <= PAGE_SIZE_TOLERANCE
            and
            abs(
                float(height)
                - A4_WIDTH_POINTS
            )
            <= PAGE_SIZE_TOLERANCE
        )

        return (
            portrait
            or landscape
        )

    @staticmethod
    def _status_from_issues(
        issues: list[
            dict[str, str]
        ],
    ) -> str:
        severities = {
            str(
                issue.get(
                    "gravidade"
                )
            )
            for issue
            in issues
        }

        if "erro" in severities:
            return "erro"

        if "atencao" in severities:
            return "atencao"

        return "ok"

    @staticmethod
    def _build_summary(
        pages: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:
        ok_pages = [
            page
            for page in pages
            if page.get(
                "status"
            )
            == "ok"
        ]

        attention_pages = [
            page
            for page in pages
            if page.get(
                "status"
            )
            == "atencao"
        ]

        error_pages = [
            page
            for page in pages
            if page.get(
                "status"
            )
            == "erro"
        ]

        total_issues = sum(
            len(
                page.get(
                    "problemas"
                )
                or []
            )
            for page
            in pages
        )

        if error_pages:
            status = "erro"

        elif attention_pages:
            status = "revisar"

        else:
            status = "ok"

        return {
            "status": status,
            "paginas_ok": len(
                ok_pages
            ),
            "paginas_atencao": len(
                attention_pages
            ),
            "paginas_erro": len(
                error_pages
            ),
            "paginas_suspeitas": (
                len(
                    attention_pages
                )
                + len(
                    error_pages
                )
            ),
            "total_alertas": (
                total_issues
            ),
        }

    @staticmethod
    def _sha256(
        path: Path,
    ) -> str:
        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as file:
            while True:
                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    @staticmethod
    def _close_if_possible(
        value: Any,
    ) -> None:
        close_method = getattr(
            value,
            "close",
            None,
        )

        if callable(
            close_method
        ):
            try:
                close_method()

            except Exception:
                pass


pdf_audit_service = (
    PDFAuditService()
)
