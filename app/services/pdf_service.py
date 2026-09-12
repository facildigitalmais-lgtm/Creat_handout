from __future__ import annotations

import hashlib
import uuid

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from pypdf import PdfReader
from weasyprint import CSS, HTML

from app.core.paths import PROJECT_ROOT
from app.core.templates import templates
from app.services.editorial_service import (
    editorial_service,
)
from app.services.project_service import (
    ProjectNotFoundError,
    ProjectValidationError,
    project_service,
)
from app.services.subject_catalog import (
    SubjectCatalogService,
    subject_catalog_service,
)


PDF_TEMPLATE = "print/pdf.html"

PDF_CSS_FILE = (
    PROJECT_ROOT
    / "static"
    / "css"
    / "pdf.css"
)

PREVIEW_PDF_FILENAME = (
    "preview.pdf"
)

A4_WIDTH_POINTS = 595.28
A4_HEIGHT_POINTS = 841.89
PAGE_SIZE_TOLERANCE = 3.0


class PDFGenerationError(
    RuntimeError
):
    pass


class PDFValidationError(
    PDFGenerationError
):
    pass


class PDFService:
    """
    Gera e valida o PDF editorial.

    Pipeline:
        projeto
        -> documento editorial intermediário
        -> primeira paginação para calcular o sumário
        -> Jinja HTML final para impressão
        -> WeasyPrint
        -> PDF temporário
        -> validação com pypdf
        -> substituição atômica
        -> atualização do project.json
    """

    def __init__(self) -> None:
        self._lock = RLock()

    def generate_preview(
        self,
        project_id: str,
        catalog: (
            SubjectCatalogService
            | None
        ) = None,
    ) -> dict[str, Any]:
        catalog = (
            catalog
            or subject_catalog_service
        )

        if not PDF_CSS_FILE.exists():
            raise PDFGenerationError(
                "Folha de estilo PDF "
                "não encontrada: "
                f"{PDF_CSS_FILE}"
            )

        with self._lock:
            document = (
                editorial_service
                .build_document(
                    project_id,
                    catalog,
                )
            )

            project_directory = (
                project_service
                .get_project_directory(
                    project_id
                )
            )

            self._prepare_cover(
                project_id=project_id,
                document=document,
            )

            self._populate_toc_pages(
                document
            )

            html_text = (
                self._render_html(
                    document
                )
            )

            final_path = (
                project_directory
                / PREVIEW_PDF_FILENAME
            )

            temp_path = (
                project_directory
                / (
                    ".preview-"
                    f"{uuid.uuid4().hex}.pdf"
                )
            )

            try:
                self._write_pdf(
                    html_text=html_text,
                    target=temp_path,
                )

                validation = (
                    self._validate_pdf(
                        temp_path
                    )
                )

                temp_path.replace(
                    final_path
                )

            except Exception as error:
                temp_path.unlink(
                    missing_ok=True
                )

                if isinstance(
                    error,
                    (
                        PDFGenerationError,
                        PDFValidationError,
                        ProjectNotFoundError,
                        ProjectValidationError,
                    ),
                ):
                    raise

                raise PDFGenerationError(
                    "Falha durante a geração "
                    "do PDF."
                ) from error

            generated_at = datetime.now(
                timezone.utc
            ).isoformat()

            metadata = {
                "arquivo": (
                    PREVIEW_PDF_FILENAME
                ),
                "gerado_em": generated_at,
                "paginas": (
                    validation[
                        "paginas"
                    ]
                ),
                "tamanho_bytes": (
                    validation[
                        "tamanho_bytes"
                    ]
                ),
                "sha256": (
                    validation[
                        "sha256"
                    ]
                ),
                "formato_paginas": (
                    validation[
                        "formato_paginas"
                    ]
                ),
                "paginas_fora_a4": (
                    validation[
                        "paginas_fora_a4"
                    ]
                ),
                "stale": False,
                "engine": "WeasyPrint",
                "template": PDF_TEMPLATE,
                "css": (
                    PDF_CSS_FILE.name
                ),
            }

            project_service.update_pdf_preview_metadata(
                project_id,
                metadata,
            )

            return metadata

    def get_preview_file(
        self,
        project_id: str,
    ) -> tuple[
        Path,
        dict[str, Any],
    ]:
        return (
            project_service
            .get_preview_pdf_file(
                project_id
            )
        )

    def _prepare_cover(
        self,
        *,
        project_id: str,
        document: dict[str, Any],
    ) -> None:
        document[
            "pdf_cover_url"
        ] = None

        cover = document.get(
            "capa"
        )

        if not isinstance(
            cover,
            dict,
        ):
            return

        try:
            cover_path, _ = (
                project_service
                .get_cover_file(
                    project_id
                )
            )

        except ProjectNotFoundError:
            return

        document[
            "pdf_cover_url"
        ] = (
            cover_path
            .resolve()
            .as_uri()
        )

    def _populate_toc_pages(
        self,
        document: dict[str, Any],
    ) -> None:
        toc = document.get(
            "sumario"
        )

        if not isinstance(
            toc,
            list,
        ):
            return

        if not toc:
            return

        html_text = self._render_html(
            document
        )

        try:
            rendered_document = HTML(
                string=html_text,
                base_url=str(
                    PROJECT_ROOT
                ),
            ).render(
                stylesheets=[
                    CSS(
                        filename=str(
                            PDF_CSS_FILE
                        )
                    )
                ],
            )

        except Exception as error:
            raise PDFGenerationError(
                "Não foi possível calcular "
                "as páginas do sumário."
            ) from error

        anchor_pages: dict[
            str,
            int,
        ] = {}

        for page_number, page in enumerate(
            rendered_document.pages,
            start=1,
        ):
            anchors = getattr(
                page,
                "anchors",
                {},
            )

            for anchor in anchors:
                anchor_pages.setdefault(
                    anchor,
                    page_number,
                )

        missing_anchors: list[str] = []

        for item in toc:
            if not isinstance(
                item,
                dict,
            ):
                continue

            anchor = str(
                item.get(
                    "anchor"
                )
                or ""
            ).strip()

            if not anchor:
                continue

            page_number = (
                anchor_pages.get(
                    anchor
                )
            )

            if page_number is None:
                missing_anchors.append(
                    anchor
                )
                continue

            item["pagina"] = (
                page_number
            )

        if missing_anchors:
            raise PDFGenerationError(
                "Não foi possível localizar "
                "todas as páginas do sumário. "
                "Âncoras ausentes: "
                + ", ".join(
                    missing_anchors[:10]
                )
            )

    def _render_html(
        self,
        document: dict[str, Any],
    ) -> str:
        try:
            template = (
                templates.env
                .get_template(
                    PDF_TEMPLATE
                )
            )

            return template.render(
                documento=document,
                show_editorial_notes=False,
            )

        except Exception as error:
            raise PDFGenerationError(
                "Não foi possível renderizar "
                "o HTML editorial do PDF."
            ) from error

    def _write_pdf(
        self,
        *,
        html_text: str,
        target: Path,
    ) -> None:
        try:
            HTML(
                string=html_text,
                base_url=str(
                    PROJECT_ROOT
                ),
            ).write_pdf(
                target=str(
                    target
                ),
                stylesheets=[
                    CSS(
                        filename=str(
                            PDF_CSS_FILE
                        )
                    )
                ],
            )

        except Exception as error:
            raise PDFGenerationError(
                "O WeasyPrint não conseguiu "
                "compor o PDF."
            ) from error

        if not target.exists():
            raise PDFGenerationError(
                "O WeasyPrint terminou sem "
                "criar o arquivo PDF."
            )

        if target.stat().st_size < 1000:
            raise PDFValidationError(
                "O PDF gerado possui tamanho "
                "anormalmente pequeno."
            )

    def _validate_pdf(
        self,
        path: Path,
    ) -> dict[str, Any]:
        try:
            reader = PdfReader(
                path,
                strict=False,
            )

            page_count = len(
                reader.pages
            )

            if page_count <= 0:
                raise PDFValidationError(
                    "O PDF não possui páginas."
                )

            page_formats: list[
                dict[str, Any]
            ] = []

            non_a4_pages: list[
                int
            ] = []

            for index, page in enumerate(
                reader.pages,
                start=1,
            ):
                width = float(
                    page.mediabox.width
                )

                height = float(
                    page.mediabox.height
                )

                page_formats.append(
                    {
                        "pagina": index,
                        "largura_pt": round(
                            width,
                            2,
                        ),
                        "altura_pt": round(
                            height,
                            2,
                        ),
                    }
                )

                portrait_a4 = (
                    abs(
                        width
                        - A4_WIDTH_POINTS
                    )
                    <= PAGE_SIZE_TOLERANCE
                    and
                    abs(
                        height
                        - A4_HEIGHT_POINTS
                    )
                    <= PAGE_SIZE_TOLERANCE
                )

                landscape_a4 = (
                    abs(
                        width
                        - A4_HEIGHT_POINTS
                    )
                    <= PAGE_SIZE_TOLERANCE
                    and
                    abs(
                        height
                        - A4_WIDTH_POINTS
                    )
                    <= PAGE_SIZE_TOLERANCE
                )

                if not (
                    portrait_a4
                    or landscape_a4
                ):
                    non_a4_pages.append(
                        index
                    )

        except PDFValidationError:
            raise

        except Exception as error:
            raise PDFValidationError(
                "O PDF foi criado, mas não "
                "pôde ser aberto e validado."
            ) from error

        size_bytes = (
            path.stat()
            .st_size
        )

        sha256 = (
            self._sha256(
                path
            )
        )

        return {
            "paginas": page_count,
            "tamanho_bytes": size_bytes,
            "sha256": sha256,
            "formato_paginas": (
                page_formats
            ),
            "paginas_fora_a4": (
                non_a4_pages
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


pdf_service = PDFService()