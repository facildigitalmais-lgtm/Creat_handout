from __future__ import annotations

from copy import deepcopy
from typing import Any


class QuestionRenderer:
    """
    Normaliza questões e gabaritos para
    representação editorial.
    """

    def normalize_question(
        self,
        question: dict[str, Any],
    ) -> dict[str, Any]:
        statement = question.get(
            "enunciado"
        )

        if not isinstance(
            statement,
            dict,
        ):
            statement = {
                "texto": (
                    ""
                    if statement is None
                    else str(statement)
                ),
                "recursos": [],
            }

        alternatives = (
            question.get(
                "alternativas"
            )
        )

        if not isinstance(
            alternatives,
            list,
        ):
            alternatives = []

        normalized_alternatives: list[
            dict[str, Any]
        ] = []

        for index, alternative in enumerate(
            alternatives,
            start=1,
        ):
            if not isinstance(
                alternative,
                dict,
            ):
                alternative = {
                    "id": str(index),
                    "ordem": index,
                    "texto": str(
                        alternative
                    ),
                }

            normalized_alternatives.append(
                {
                    "id": (
                        alternative.get(
                            "id"
                        )
                        or str(index)
                    ),
                    "ordem": (
                        alternative.get(
                            "ordem",
                            index,
                        )
                    ),
                    "texto": str(
                        alternative.get(
                            "texto"
                        )
                        or ""
                    ),
                }
            )

        normalized_alternatives.sort(
            key=lambda item: (
                self._integer(
                    item.get(
                        "ordem"
                    )
                )
            )
        )

        return {
            "id": question.get("id"),
            "ordem": question.get(
                "ordem",
                0,
            ),
            "tipo": question.get(
                "tipo",
                "questao",
            ),
            "dificuldade": question.get(
                "dificuldade"
            ),
            "nivel_cognitivo": (
                question.get(
                    "nivel_cognitivo"
                )
            ),
            "enunciado": str(
                statement.get(
                    "texto"
                )
                or ""
            ),
            "recursos": (
                statement.get(
                    "recursos"
                )
                if isinstance(
                    statement.get(
                        "recursos"
                    ),
                    list,
                )
                else []
            ),
            "alternativas": (
                normalized_alternatives
            ),
            "tags": (
                deepcopy(
                    question.get(
                        "tags"
                    )
                )
                if isinstance(
                    question.get(
                        "tags"
                    ),
                    list,
                )
                else []
            ),
        }

    def normalize_answer(
        self,
        answer: dict[str, Any],
        *,
        question_number: int | None = None,
    ) -> dict[str, Any]:
        analyses = answer.get(
            "analise_alternativas"
        )

        if not isinstance(
            analyses,
            list,
        ):
            analyses = []

        normalized_analyses: list[
            dict[str, Any]
        ] = []

        for item in analyses:
            if not isinstance(
                item,
                dict,
            ):
                continue

            normalized_analyses.append(
                {
                    "alternativa_id": (
                        item.get(
                            "alternativa_id"
                        )
                    ),
                    "correta": bool(
                        item.get(
                            "correta",
                            False,
                        )
                    ),
                    "comentario": str(
                        item.get(
                            "comentario"
                        )
                        or ""
                    ),
                }
            )

        return {
            "question_id": (
                answer.get(
                    "question_id"
                )
            ),
            "question_number": (
                question_number
            ),
            "resposta": (
                answer.get(
                    "resposta"
                )
            ),
            "comentario": str(
                answer.get(
                    "comentario"
                )
                or ""
            ),
            "fundamento": str(
                answer.get(
                    "fundamento"
                )
                or ""
            ),
            "resolucao": str(
                answer.get(
                    "resolucao"
                )
                or ""
            ),
            "erro_provavel": str(
                answer.get(
                    "erro_provavel"
                )
                or ""
            ),
            "analise_alternativas": (
                normalized_analyses
            ),
        }

    @staticmethod
    def _integer(
        value: Any,
    ) -> int:
        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return 999999


question_renderer = QuestionRenderer()