from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.renderers.block_renderer import (
    block_renderer,
)
from app.renderers.question_renderer import (
    question_renderer,
)
from app.renderers.reference_renderer import (
    reference_renderer,
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


class EditorialService:
    """
    Constrói a representação editorial intermediária
    usada por HTML e, posteriormente, PDF.

    Esta camada não conhece Português, Matemática,
    História, Microbiologia ou qualquer outra matéria.

    Ela trabalha apenas com:

    - hierarquia;
    - blocos;
    - exercícios;
    - gabaritos;
    - referências;
    - configuração editorial do projeto.
    """

    def build_document(
        self,
        project_id: str,
        catalog: SubjectCatalogService | None = None,
    ) -> dict[str, Any]:
        catalog = (
            catalog
            or subject_catalog_service
        )

        project = project_service.get_project(
            project_id,
            catalog,
        )

        integrity = project.get(
            "integridade"
        )

        if (
            isinstance(
                integrity,
                dict,
            )
            and not integrity.get(
                "ok",
                False,
            )
        ):
            raise ProjectValidationError(
                "O projeto contém matérias "
                "ausentes ou inválidas. "
                "Corrija a biblioteca antes "
                "de gerar a prévia."
            )

        project_subjects = project.get(
            "materias"
        )

        if not isinstance(
            project_subjects,
            list,
        ):
            project_subjects = []

        if not project_subjects:
            raise ProjectValidationError(
                "O projeto não possui matérias "
                "selecionadas."
            )

        editorial = project.get(
            "editorial"
        )

        if not isinstance(
            editorial,
            dict,
        ):
            editorial = {}

        ordered_subjects = sorted(
            project_subjects,
            key=lambda item: (
                self._integer(
                    item.get(
                        "ordem"
                    )
                )
            ),
        )

        subjects: list[
            dict[str, Any]
        ] = []

        global_exercises: list[
            dict[str, Any]
        ] = []

        global_answers: list[
            dict[str, Any]
        ] = []

        consolidated_references: list[
            dict[str, Any]
        ] = []

        reference_keys: set[
            str
        ] = set()

        for subject_index, project_subject in enumerate(
            ordered_subjects,
            start=1,
        ):
            subject_id = (
                project_subject.get(
                    "id_materia"
                )
            )

            if not isinstance(
                subject_id,
                str,
            ) or not subject_id:
                raise ProjectValidationError(
                    "O projeto contém uma matéria "
                    "sem id_materia válido."
                )

            try:
                document = (
                    catalog.get_subject_document(
                        subject_id
                    )
                )

            except (
                KeyError,
                FileNotFoundError,
                ValueError,
            ) as error:
                raise ProjectNotFoundError(
                    "Não foi possível carregar "
                    f"a matéria {subject_id!r}."
                ) from error

            subject = self._build_subject(
                project_subject=project_subject,
                document=document,
                subject_index=subject_index,
            )

            if (
                editorial.get(
                    "exercises_position"
                )
                == "end_document"
            ):
                global_exercises.extend(
                    subject[
                        "exercicios"
                    ]
                )

                subject[
                    "exercicios"
                ] = []

            if (
                editorial.get(
                    "answers_position"
                )
                == "end_document"
            ):
                global_answers.extend(
                    subject[
                        "gabaritos"
                    ]
                )

                subject[
                    "gabaritos"
                ] = []

            if (
                editorial.get(
                    "references_position"
                )
                == "end_document"
            ):
                for reference in subject[
                    "referencias"
                ]:
                    key = (
                        reference_renderer
                        .deduplication_key(
                            reference
                        )
                    )

                    if key in reference_keys:
                        continue

                    reference_keys.add(
                        key
                    )

                    consolidated_references.append(
                        reference
                    )

                subject[
                    "referencias"
                ] = []

            subjects.append(
                subject
            )

        toc = self._build_toc(
            subjects=subjects,
            editorial=editorial,
        )

        return {
            "project": project,
            "dados": deepcopy(
                project.get(
                    "dados"
                )
                or {}
            ),
            "editorial": deepcopy(
                editorial
            ),
            "capa": deepcopy(
                project.get(
                    "capa"
                )
            ),
            "cover_url": (
                project.get(
                    "cover_url"
                )
            ),
            "sumario": toc,
            "materias": subjects,
            "exercicios_finais": (
                global_exercises
            ),
            "gabaritos_finais": (
                global_answers
            ),
            "referencias_finais": (
                consolidated_references
            ),
            "estatisticas": (
                self._document_statistics(
                    subjects=subjects,
                    final_exercises=(
                        global_exercises
                    ),
                    final_answers=(
                        global_answers
                    ),
                    final_references=(
                        consolidated_references
                    ),
                )
            ),
        }

    def _build_subject(
        self,
        *,
        project_subject: dict[str, Any],
        document: dict[str, Any],
        subject_index: int,
    ) -> dict[str, Any]:
        header = document.get(
            "cabecalho"
        )

        if not isinstance(
            header,
            dict,
        ):
            header = {}

        structure = document.get(
            "mapa_estrutura"
        )

        if not isinstance(
            structure,
            list,
        ):
            structure = []

        content = document.get(
            "conteudo"
        )

        if not isinstance(
            content,
            list,
        ):
            content = []

        assets = document.get(
            "assets"
        )

        if not isinstance(
            assets,
            list,
        ):
            assets = []

        assets_by_id = {
            str(
                item.get("id")
            ): item
            for item in assets
            if (
                isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "id"
                )
            )
        }

        numbering = (
            self._build_section_numbering(
                structure
            )
        )

        structure_by_id = {
            str(
                item.get("id")
            ): item
            for item in structure
            if (
                isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "id"
                )
            )
        }

        content_by_section: dict[
            str,
            dict[str, Any],
        ] = {}

        for item in content:
            if not isinstance(
                item,
                dict,
            ):
                continue

            section_id = (
                item.get(
                    "section_id"
                )
            )

            if isinstance(
                section_id,
                str,
            ):
                content_by_section[
                    section_id
                ] = item

        ordered_structure = (
            self._ordered_structure(
                structure
            )
        )

        sections: list[
            dict[str, Any]
        ] = []

        for section in ordered_structure:
            section_id = str(
                section.get(
                    "id"
                )
            )

            content_section = (
                content_by_section.get(
                    section_id,
                    {},
                )
            )

            blocks = content_section.get(
                "blocos"
            )

            if not isinstance(
                blocks,
                list,
            ):
                blocks = []

            normalized_blocks: list[
                dict[str, Any]
            ] = []

            for block in sorted(
                blocks,
                key=lambda item: (
                    self._integer(
                        item.get(
                            "ordem"
                        )
                    )
                    if isinstance(
                        item,
                        dict,
                    )
                    else 999999
                ),
            ):
                if not isinstance(
                    block,
                    dict,
                ):
                    continue

                if (
                    block.get(
                        "visibilidade"
                    )
                    != "aluno"
                ):
                    continue

                normalized_blocks.append(
                    block_renderer.normalize(
                        block,
                        assets_by_id=(
                            assets_by_id
                        ),
                    )
                )

            sections.append(
                {
                    "id": section_id,
                    "numero": (
                        numbering.get(
                            section_id,
                            "",
                        )
                    ),
                    "titulo": str(
                        section.get(
                            "titulo"
                        )
                        or
                        section_id
                    ),
                    "descricao": str(
                        section.get(
                            "descricao"
                        )
                        or ""
                    ),
                    "nivel": (
                        self._integer(
                            section.get(
                                "nivel"
                            )
                        )
                    ),
                    "tipo": (
                        section.get(
                            "tipo"
                        )
                    ),
                    "parent_id": (
                        section.get(
                            "parent_id"
                        )
                    ),
                    "anchor": (
                        self._anchor(
                            project_subject.get(
                                "id_materia"
                            ),
                            section_id,
                        )
                    ),
                    "blocos": (
                        normalized_blocks
                    ),
                }
            )

        raw_questions = document.get(
            "exercicios"
        )

        if not isinstance(
            raw_questions,
            list,
        ):
            raw_questions = []

        exercises: list[
            dict[str, Any]
        ] = []

        question_number_by_id: dict[
            str,
            int,
        ] = {}

        for number, question in enumerate(
            sorted(
                (
                    item
                    for item
                    in raw_questions
                    if isinstance(
                        item,
                        dict,
                    )
                ),
                key=lambda item: (
                    self._integer(
                        item.get(
                            "ordem"
                        )
                    )
                ),
            ),
            start=1,
        ):
            normalized = (
                question_renderer
                .normalize_question(
                    question
                )
            )

            normalized[
                "numero"
            ] = number

            normalized[
                "materia"
            ] = (
                project_subject.get(
                    "materia"
                )
                or header.get(
                    "materia"
                )
            )

            normalized[
                "materia_ordem"
            ] = subject_index

            exercises.append(
                normalized
            )

            question_id = (
                normalized.get(
                    "id"
                )
            )

            if isinstance(
                question_id,
                str,
            ):
                question_number_by_id[
                    question_id
                ] = number

        raw_answers = document.get(
            "gabaritos"
        )

        if not isinstance(
            raw_answers,
            list,
        ):
            raw_answers = []

        answers: list[
            dict[str, Any]
        ] = []

        for answer in raw_answers:
            if not isinstance(
                answer,
                dict,
            ):
                continue

            question_id = (
                answer.get(
                    "question_id"
                )
            )

            normalized_answer = (
                question_renderer
                .normalize_answer(
                    answer,
                    question_number=(
                        question_number_by_id
                        .get(
                            str(
                                question_id
                            )
                        )
                    ),
                )
            )

            normalized_answer[
                "materia"
            ] = (
                project_subject.get(
                    "materia"
                )
                or header.get(
                    "materia"
                )
            )

            normalized_answer[
                "materia_ordem"
            ] = subject_index

            answers.append(
                normalized_answer
            )

        raw_references = document.get(
            "referencias"
        )

        if not isinstance(
            raw_references,
            list,
        ):
            raw_references = []

        references = [
            reference_renderer.normalize(
                item
            )
            for item in sorted(
                (
                    reference
                    for reference
                    in raw_references
                    if isinstance(
                        reference,
                        dict,
                    )
                ),
                key=lambda item: (
                    self._integer(
                        item.get(
                            "ordem"
                        )
                    )
                ),
            )
        ]

        return {
            "id_materia": (
                project_subject.get(
                    "id_materia"
                )
            ),
            "codigo_materia": (
                project_subject.get(
                    "codigo_materia"
                )
                or header.get(
                    "codigo_materia"
                )
            ),
            "ordem": subject_index,
            "materia": (
                project_subject.get(
                    "materia"
                )
                or header.get(
                    "materia"
                )
                or "Matéria"
            ),
            "titulo": (
                header.get(
                    "titulo_sugerido"
                )
                or project_subject.get(
                    "materia"
                )
                or "Matéria"
            ),
            "subtitulo": (
                header.get(
                    "subtitulo_sugerido"
                )
            ),
            "descricao": (
                header.get(
                    "descricao"
                )
                or ""
            ),
            "anchor": (
                f"materia-{subject_index}"
            ),
            "secoes": sections,
            "exercicios": exercises,
            "gabaritos": answers,
            "referencias": references,
            "total_secoes": len(
                structure_by_id
            ),
            "total_blocos": sum(
                len(
                    section[
                        "blocos"
                    ]
                )
                for section
                in sections
            ),
        }

    def _build_section_numbering(
        self,
        structure: list[Any],
    ) -> dict[str, str]:
        items = [
            item
            for item in structure
            if (
                isinstance(
                    item,
                    dict,
                )
                and isinstance(
                    item.get(
                        "id"
                    ),
                    str,
                )
            )
        ]

        children: dict[
            str | None,
            list[dict[str, Any]],
        ] = {}

        for item in items:
            parent_id = (
                item.get(
                    "parent_id"
                )
            )

            if not isinstance(
                parent_id,
                str,
            ):
                parent_id = None

            children.setdefault(
                parent_id,
                [],
            ).append(
                item
            )

        for siblings in (
            children.values()
        ):
            siblings.sort(
                key=lambda item: (
                    self._integer(
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

        numbering: dict[
            str,
            str,
        ] = {}

        visited: set[
            str
        ] = set()

        def walk(
            parent_id: str | None,
            prefix: tuple[int, ...],
        ) -> None:
            siblings = children.get(
                parent_id,
                [],
            )

            for position, item in enumerate(
                siblings,
                start=1,
            ):
                item_id = str(
                    item.get(
                        "id"
                    )
                )

                if item_id in visited:
                    continue

                visited.add(
                    item_id
                )

                number_tuple = (
                    prefix
                    + (
                        position,
                    )
                )

                numbering[
                    item_id
                ] = ".".join(
                    str(part)
                    for part
                    in number_tuple
                )

                walk(
                    item_id,
                    number_tuple,
                )

        walk(
            None,
            (),
        )

        for item in items:
            item_id = str(
                item.get(
                    "id"
                )
            )

            if item_id in visited:
                continue

            numbering[
                item_id
            ] = str(
                len(
                    numbering
                )
                + 1
            )

        return numbering

    def _ordered_structure(
        self,
        structure: list[Any],
    ) -> list[
        dict[str, Any]
    ]:
        items = [
            item
            for item in structure
            if isinstance(
                item,
                dict,
            )
        ]

        children: dict[
            str | None,
            list[dict[str, Any]],
        ] = {}

        for item in items:
            parent = item.get(
                "parent_id"
            )

            if not isinstance(
                parent,
                str,
            ):
                parent = None

            children.setdefault(
                parent,
                [],
            ).append(
                item
            )

        for siblings in (
            children.values()
        ):
            siblings.sort(
                key=lambda item: (
                    self._integer(
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

        ordered: list[
            dict[str, Any]
        ] = []

        visited: set[
            str
        ] = set()

        def walk(
            parent: str | None,
        ) -> None:
            for item in children.get(
                parent,
                [],
            ):
                item_id = str(
                    item.get(
                        "id"
                    )
                )

                if item_id in visited:
                    continue

                visited.add(
                    item_id
                )

                ordered.append(
                    item
                )

                walk(
                    item_id
                )

        walk(
            None
        )

        for item in items:
            item_id = str(
                item.get(
                    "id"
                )
            )

            if item_id not in visited:
                ordered.append(
                    item
                )

        return ordered

    def _build_toc(
        self,
        *,
        subjects: list[dict[str, Any]],
        editorial: dict[str, Any],
    ) -> list[
        dict[str, Any]
    ]:
        include_level_2 = bool(
            editorial.get(
                "toc_level_2",
                True,
            )
        )

        include_level_3 = bool(
            editorial.get(
                "toc_level_3",
                True,
            )
        )

        include_level_4 = bool(
            editorial.get(
                "toc_level_4",
                False,
            )
        )

        toc: list[
            dict[str, Any]
        ] = []

        for subject in subjects:
            entry = {
                "tipo": "materia",
                "nivel": 0,
                "numero": str(
                    subject[
                        "ordem"
                    ]
                ),
                "titulo": (
                    subject[
                        "materia"
                    ]
                ),
                "anchor": (
                    subject[
                        "anchor"
                    ]
                ),
            }

            toc.append(
                entry
            )

            for section in subject[
                "secoes"
            ]:
                level = (
                    section[
                        "nivel"
                    ]
                )

                include = False

                if (
                    level == 1
                    and include_level_2
                ):
                    include = True

                elif (
                    level == 2
                    and include_level_3
                ):
                    include = True

                elif (
                    level >= 3
                    and include_level_4
                ):
                    include = True

                if not include:
                    continue

                toc.append(
                    {
                        "tipo": "secao",
                        "nivel": level,
                        "numero": (
                            section[
                                "numero"
                            ]
                        ),
                        "titulo": (
                            section[
                                "titulo"
                            ]
                        ),
                        "anchor": (
                            section[
                                "anchor"
                            ]
                        ),
                    }
                )

        return toc

    def _document_statistics(
        self,
        *,
        subjects: list[dict[str, Any]],
        final_exercises: list[dict[str, Any]],
        final_answers: list[dict[str, Any]],
        final_references: list[dict[str, Any]],
    ) -> dict[str, int]:
        subject_exercises = sum(
            len(
                subject[
                    "exercicios"
                ]
            )
            for subject
            in subjects
        )

        subject_answers = sum(
            len(
                subject[
                    "gabaritos"
                ]
            )
            for subject
            in subjects
        )

        subject_references = sum(
            len(
                subject[
                    "referencias"
                ]
            )
            for subject
            in subjects
        )

        return {
            "materias": len(
                subjects
            ),
            "secoes": sum(
                len(
                    subject[
                        "secoes"
                    ]
                )
                for subject
                in subjects
            ),
            "blocos": sum(
                subject[
                    "total_blocos"
                ]
                for subject
                in subjects
            ),
            "exercicios": (
                subject_exercises
                + len(
                    final_exercises
                )
            ),
            "gabaritos": (
                subject_answers
                + len(
                    final_answers
                )
            ),
            "referencias": (
                subject_references
                + len(
                    final_references
                )
            ),
        }

    @staticmethod
    def _anchor(
        subject_id: Any,
        section_id: str,
    ) -> str:
        raw = (
            f"{subject_id}-{section_id}"
        )

        return (
            raw
            .replace(".", "-")
            .replace("_", "-")
            .replace(" ", "-")
        )

    @staticmethod
    def _integer(
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


editorial_service = EditorialService()