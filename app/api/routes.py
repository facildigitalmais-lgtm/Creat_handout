from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
)

from app.core.settings import get_settings
from app.core.templates import templates
from app.models.project import ProjectPayload
from app.services.editorial_service import editorial_service
from app.services.pdf_audit_service import (
    PDFAuditError,
    pdf_audit_service,
)
from app.services.pdf_service import (
    PDFGenerationError,
    PDFValidationError,
    pdf_service,
)
from app.services.project_service import (
    CoverValidationError,
    ProjectError,
    ProjectNotFoundError,
    ProjectValidationError,
    project_service,
)
from app.services.prompt_service import prompt_service
from app.services.subject_catalog import subject_catalog_service


router = APIRouter()


@router.get(
    "/",
    response_class=HTMLResponse,
    name="home",
)
async def home(
    request: Request,
) -> HTMLResponse:
    settings = get_settings()
    snapshot = subject_catalog_service.snapshot()
    materias = subject_catalog_service.list_subjects()

    return templates.TemplateResponse(
        request=request,
        name="pages/workspace.html",
        context={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "editor": settings.editor,
            "catalogo": snapshot,
            "materias": materias,
        },
    )


@router.get(
    "/api/health",
    name="api_health",
)
async def api_health() -> dict[str, object]:
    settings = get_settings()
    snapshot = subject_catalog_service.snapshot()

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "biblioteca": snapshot["estatisticas"],
        "carregado_em": snapshot["carregado_em"],
    }


@router.get(
    "/api/catalogo",
    name="api_catalogo",
)
async def api_catalogo() -> dict[str, object]:
    return subject_catalog_service.snapshot()


@router.get(
    "/projetos/{project_id}/preview",
    response_class=HTMLResponse,
    name="project_preview",
)
async def project_preview(
    request: Request,
    project_id: str,
) -> HTMLResponse:
    try:
        document = editorial_service.build_document(
            project_id,
            subject_catalog_service,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return templates.TemplateResponse(
        request=request,
        name="print/preview.html",
        context={
            "documento": document,
            "show_editorial_notes": False,
        },
    )


@router.post(
    "/api/projetos/{project_id}/pdf/preview",
    name="api_gerar_pdf_preview",
)
def api_gerar_pdf_preview(
    project_id: str,
) -> dict[str, object]:
    try:
        metadata = pdf_service.generate_preview(
            project_id,
            subject_catalog_service,
        )

        audit = pdf_audit_service.audit_preview(
            project_id
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ProjectValidationError,
        PDFValidationError,
        PDFGenerationError,
        PDFAuditError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "pdf": metadata,
        "audit": audit,
        "view_url": (
            f"/api/projetos/"
            f"{project_id}/pdf/preview"
        ),
        "download_url": (
            f"/api/projetos/"
            f"{project_id}/pdf/download"
        ),
    }


@router.get(
    "/api/projetos/{project_id}/pdf/preview",
    name="api_visualizar_pdf_preview",
)
async def api_visualizar_pdf_preview(
    project_id: str,
) -> FileResponse:
    try:
        path, metadata = (
            pdf_service.get_preview_file(
                project_id
            )
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="preview.pdf",
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store",
            "X-PDF-Pages": str(
                metadata.get(
                    "paginas",
                    "",
                )
            ),
        },
    )


@router.get(
    "/api/projetos/{project_id}/pdf/download",
    name="api_baixar_pdf_preview",
)
async def api_baixar_pdf_preview(
    project_id: str,
) -> FileResponse:
    try:
        path, _ = (
            pdf_service.get_preview_file(
                project_id
            )
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="Apostila_Preview.pdf",
        content_disposition_type="attachment",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/api/projetos/{project_id}/pdf/audit",
    name="api_obter_auditoria_pdf",
)
def api_obter_auditoria_pdf(
    project_id: str,
) -> dict[str, object]:
    try:
        audit = pdf_audit_service.get_audit(
            project_id
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ProjectError,
        PDFAuditError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "audit": audit,
    }


@router.post(
    "/api/projetos/{project_id}/pdf/audit",
    name="api_executar_auditoria_pdf",
)
def api_executar_auditoria_pdf(
    project_id: str,
) -> dict[str, object]:
    try:
        audit = pdf_audit_service.audit_preview(
            project_id
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ProjectError,
        PDFAuditError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "audit": audit,
    }


@router.get(
    "/api/projetos/{project_id}/pdf/audit/pages/{page_number}",
    response_class=FileResponse,
    name="api_miniatura_auditoria_pdf",
)
def api_miniatura_auditoria_pdf(
    project_id: str,
    page_number: int,
) -> FileResponse:
    try:
        path = pdf_audit_service.get_thumbnail(
            project_id,
            page_number,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except (
        ProjectError,
        PDFAuditError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return FileResponse(
        path=path,
        media_type="image/jpeg",
        filename=path.name,
        content_disposition_type="inline",
        headers={
            "Cache-Control": "no-store",
        },
    )


@router.get(
    "/api/projetos",
    name="api_projetos",
)
async def api_projetos() -> dict[str, object]:
    return project_service.list_projects()


@router.post(
    "/api/projetos",
    name="api_salvar_projeto",
)
async def api_salvar_projeto(
    payload: ProjectPayload,
) -> dict[str, object]:
    try:
        project = project_service.save_project(
            payload,
            subject_catalog_service,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "projeto": project,
    }


@router.get(
    "/api/projetos/{project_id}",
    name="api_abrir_projeto",
)
async def api_abrir_projeto(
    project_id: str,
) -> dict[str, object]:
    try:
        project = project_service.get_project(
            project_id,
            subject_catalog_service,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "projeto": project,
    }


@router.delete(
    "/api/projetos/{project_id}",
    name="api_excluir_projeto",
)
async def api_excluir_projeto(
    project_id: str,
) -> dict[str, object]:
    try:
        project_service.delete_project(
            project_id
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "mensagem": "Projeto excluído.",
    }


@router.post(
    "/api/projetos/{project_id}/capa",
    name="api_salvar_capa_projeto",
)
def api_salvar_capa_projeto(
    project_id: str,
    file: UploadFile = File(...),
) -> dict[str, object]:
    try:
        project = project_service.save_cover(
            project_id=project_id,
            file_obj=file.file,
            filename=file.filename,
            content_type=file.content_type,
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except CoverValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "projeto": project,
    }


@router.get(
    "/api/projetos/{project_id}/capa",
    response_class=FileResponse,
    name="api_capa_projeto",
)
async def api_capa_projeto(
    project_id: str,
) -> FileResponse:
    try:
        path, mime_type = (
            project_service.get_cover_file(
                project_id
            )
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return FileResponse(
        path=path,
        media_type=mime_type,
    )


@router.delete(
    "/api/projetos/{project_id}/capa",
    name="api_excluir_capa_projeto",
)
async def api_excluir_capa_projeto(
    project_id: str,
) -> dict[str, object]:
    try:
        project = project_service.delete_cover(
            project_id
        )

    except ProjectNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ProjectError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "ok": True,
        "projeto": project,
    }


@router.get(
    "/api/prompts/converter-materia",
    response_class=PlainTextResponse,
    name="api_prompt_converter_materia",
)
async def api_prompt_converter_materia() -> PlainTextResponse:
    prompt = prompt_service.get_converter_prompt()

    return PlainTextResponse(
        content=prompt,
        media_type="text/plain; charset=utf-8",
    )


@router.post(
    "/api/catalogo/recarregar",
    name="api_catalogo_recarregar",
)
async def api_catalogo_recarregar() -> JSONResponse:
    snapshot = subject_catalog_service.reload()

    return JSONResponse(
        {
            "ok": True,
            "mensagem": "Biblioteca recarregada com sucesso.",
            "catalogo": snapshot,
        }
    )