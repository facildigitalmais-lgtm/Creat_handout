from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProjectData(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    titulo: str = Field(
        min_length=1,
        max_length=300,
    )

    concurso: str = Field(
        default="",
        max_length=500,
    )

    orgao: str = Field(
        default="",
        max_length=300,
    )

    banca: str = Field(
        default="",
        max_length=200,
    )

    cargo: str = Field(
        default="",
        max_length=500,
    )

    ano: str | None = Field(
        default=None,
        max_length=30,
    )

    edicao: str = Field(
        default="",
        max_length=100,
    )

    editora: str = Field(
        default="",
        max_length=300,
    )

    site: str = Field(
        default="",
        max_length=500,
    )

    pagina_rosto: str = Field(
        default="",
        max_length=20000,
    )

    aviso_legal: str = Field(
        default="",
        max_length=20000,
    )


class ProjectSubject(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    id_materia: str = Field(
        min_length=1,
        max_length=300,
    )

    ordem: int = Field(
        ge=1,
    )

    materia: str | None = Field(
        default=None,
        max_length=500,
    )

    codigo_materia: str | None = Field(
        default=None,
        max_length=50,
    )


class EditorialSettings(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    cover_mode: str = Field(
        default="cover",
        pattern="^(cover|contain)$",
    )

    exercises_position: str = Field(
        default="after_subject",
        pattern="^(after_subject|end_document)$",
    )

    answers_position: str = Field(
        default="end_document",
        pattern="^(after_subject|end_document)$",
    )

    references_position: str = Field(
        default="end_document",
        pattern="^(after_subject|end_document)$",
    )

    subject_new_page: bool = True

    toc_level_2: bool = True
    toc_level_3: bool = True
    toc_level_4: bool = False


class ProjectPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    project_id: str | None = Field(
        default=None,
        pattern="^[a-f0-9]{12}$",
    )

    dados: ProjectData

    materias: list[ProjectSubject] = Field(
        default_factory=list,
    )

    editorial: EditorialSettings = Field(
        default_factory=EditorialSettings,
    )