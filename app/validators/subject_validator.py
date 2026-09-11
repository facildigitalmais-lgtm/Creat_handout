from __future__ import annotations

import json

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator


class SubjectValidator:
    """
    Validador estrutural e semântico de uma matéria completa.

    Cada documento validado por esta classe representa:

        1 arquivo JSON = 1 matéria completa.

    A validação ocorre em duas etapas:

    1. Validação pelo JSON Schema Draft 2020-12.
    2. Validação semântica das referências internas.

    A segunda etapa verifica, entre outros pontos:

    - IDs duplicados;
    - hierarquia do mapa de estrutura;
    - ciclos de parent_id;
    - section_id inexistente;
    - objetivos inexistentes;
    - fontes inexistentes;
    - assets inexistentes;
    - recursos inexistentes;
    - questões sem gabarito;
    - gabaritos órfãos;
    - respostas de múltipla escolha inválidas;
    - referências cruzadas inconsistentes.
    """

    def __init__(
        self,
        schema_path: Path,
    ) -> None:
        self.schema_path = schema_path

        self.schema = self._load_schema(
            schema_path
        )

        self.validator = (
            Draft202012Validator(
                self.schema
            )
        )

    @staticmethod
    def _load_schema(
        schema_path: Path,
    ) -> dict[str, Any]:
        """
        Carrega e valida o próprio JSON Schema.
        """

        if not schema_path.exists():
            raise FileNotFoundError(
                "JSON Schema não encontrado: "
                f"{schema_path}"
            )

        try:
            with schema_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                schema = json.load(
                    file
                )

        except json.JSONDecodeError as error:
            raise ValueError(
                "O arquivo de JSON Schema "
                "possui JSON inválido: "
                f"linha {error.lineno}, "
                f"coluna {error.colno}: "
                f"{error.msg}"
            ) from error

        except OSError as error:
            raise OSError(
                "Não foi possível ler "
                "o JSON Schema: "
                f"{schema_path}"
            ) from error

        if not isinstance(
            schema,
            dict,
        ):
            raise ValueError(
                "O JSON Schema deve possuir "
                "um objeto JSON na raiz."
            )

        Draft202012Validator.check_schema(
            schema
        )

        return schema

    @staticmethod
    def _format_json_path(
        path: Iterable[Any],
    ) -> str:
        """
        Converte caminhos produzidos pelo
        jsonschema para uma representação
        legível semelhante a JSONPath.
        """

        parts = list(path)

        if not parts:
            return "$"

        result = "$"

        for item in parts:
            if isinstance(
                item,
                int,
            ):
                result += (
                    f"[{item}]"
                )

            else:
                result += (
                    f".{item}"
                )

        return result

    def validate(
        self,
        document: dict[str, Any],
    ) -> list[str]:
        """
        Executa todas as validações.

        Retorna uma lista vazia quando
        o documento é considerado válido.
        """

        errors: list[str] = []

        errors.extend(
            self._validate_schema(
                document
            )
        )

        errors.extend(
            self._validate_semantics(
                document
            )
        )

        return self._deduplicate_errors(
            errors
        )

    def _validate_schema(
        self,
        document: dict[str, Any],
    ) -> list[str]:
        """
        Executa a validação formal contra
        o JSON Schema configurado.
        """

        errors: list[str] = []

        validation_errors = sorted(
            self.validator.iter_errors(
                document
            ),
            key=lambda error: (
                list(
                    error.absolute_path
                )
            ),
        )

        for error in validation_errors:
            path = (
                self._format_json_path(
                    error.absolute_path
                )
            )

            errors.append(
                f"{path}: {error.message}"
            )

        return errors

    def _validate_semantics(
        self,
        document: dict[str, Any],
    ) -> list[str]:
        """
        Valida relacionamentos que não são
        convenientemente expressos apenas
        pelo JSON Schema.
        """

        errors: list[str] = []

        if not isinstance(
            document,
            dict,
        ):
            return [
                "O documento deve possuir "
                "um objeto JSON na raiz."
            ]

        cabecalho = document.get(
            "cabecalho"
        )

        if not isinstance(
            cabecalho,
            dict,
        ):
            return errors

        map_items = self._list_value(
            document,
            "mapa_estrutura",
        )

        summary_items = self._list_value(
            cabecalho,
            "estrutura_resumida",
        )

        objective_items = self._list_value(
            document,
            "objetivos_aprendizagem",
        )

        source_items = self._list_value(
            document,
            "fontes",
        )

        asset_items = self._list_value(
            document,
            "assets",
        )

        content_items = self._list_value(
            document,
            "conteudo",
        )

        question_items = self._list_value(
            document,
            "exercicios",
        )

        answer_items = self._list_value(
            document,
            "gabaritos",
        )

        reference_items = self._list_value(
            document,
            "referencias",
        )

        map_ids = self._ids_from(
            map_items
        )

        objective_ids = self._ids_from(
            objective_items
        )

        source_ids = self._ids_from(
            source_items
        )

        asset_ids = self._ids_from(
            asset_items
        )

        question_ids = self._ids_from(
            question_items
        )

        reference_ids = self._ids_from(
            reference_items
        )

        block_ids = (
            self._collect_block_ids(
                content_items
            )
        )

        errors.extend(
            self._validate_duplicate_ids(
                cabecalho=cabecalho,
                map_items=map_items,
                objective_items=(
                    objective_items
                ),
                source_items=(
                    source_items
                ),
                asset_items=(
                    asset_items
                ),
                content_items=(
                    content_items
                ),
                question_items=(
                    question_items
                ),
                reference_items=(
                    reference_items
                ),
            )
        )

        errors.extend(
            self._validate_map_relationships(
                map_items=map_items,
                map_ids=map_ids,
            )
        )

        errors.extend(
            self._validate_summary_relationships(
                summary_items=(
                    summary_items
                ),
                map_ids=map_ids,
            )
        )

        errors.extend(
            self._validate_content_sections(
                content_items=(
                    content_items
                ),
                map_ids=map_ids,
            )
        )

        errors.extend(
            self._validate_question_answers(
                questions=(
                    question_items
                ),
                answers=(
                    answer_items
                ),
            )
        )

        errors.extend(
            self._validate_cross_references(
                document=document,
                map_ids=map_ids,
                objective_ids=(
                    objective_ids
                ),
                source_ids=(
                    source_ids
                ),
                asset_ids=(
                    asset_ids
                ),
                block_ids=(
                    block_ids
                ),
                question_ids=(
                    question_ids
                ),
                reference_ids=(
                    reference_ids
                ),
            )
        )

        return errors

    @staticmethod
    def _list_value(
        obj: dict[str, Any],
        key: str,
    ) -> list[Any]:
        """
        Obtém uma propriedade somente quando
        ela realmente é uma lista.
        """

        value = obj.get(
            key
        )

        if isinstance(
            value,
            list,
        ):
            return value

        return []

    @staticmethod
    def _ids_from(
        items: list[Any],
    ) -> set[str]:
        """
        Extrai IDs válidos de uma coleção.
        """

        result: set[str] = set()

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = item.get(
                "id"
            )

            if (
                isinstance(
                    item_id,
                    str,
                )
                and
                item_id.strip()
            ):
                result.add(
                    item_id
                )

        return result

    @staticmethod
    def _collect_block_ids(
        content_items: list[Any],
    ) -> set[str]:
        """
        Extrai IDs de todos os blocos de
        conteúdo da matéria.
        """

        ids: set[str] = set()

        for section in content_items:
            if not isinstance(
                section,
                dict,
            ):
                continue

            blocks = section.get(
                "blocos"
            )

            if not isinstance(
                blocks,
                list,
            ):
                continue

            for block in blocks:
                if not isinstance(
                    block,
                    dict,
                ):
                    continue

                block_id = block.get(
                    "id"
                )

                if (
                    isinstance(
                        block_id,
                        str,
                    )
                    and
                    block_id.strip()
                ):
                    ids.add(
                        block_id
                    )

        return ids

    @staticmethod
    def _validate_duplicate_ids(
        *,
        cabecalho: dict[str, Any],
        map_items: list[Any],
        objective_items: list[Any],
        source_items: list[Any],
        asset_items: list[Any],
        content_items: list[Any],
        question_items: list[Any],
        reference_items: list[Any],
    ) -> list[str]:
        """
        Verifica IDs globais duplicados.

        IDs de alternativas não entram nesta
        verificação porque letras como A, B,
        C e D podem legitimamente aparecer
        em várias questões.
        """

        values: list[str] = []

        subject_id = cabecalho.get(
            "id_materia"
        )

        if (
            isinstance(
                subject_id,
                str,
            )
            and
            subject_id.strip()
        ):
            values.append(
                subject_id
            )

        collections = (
            map_items,
            objective_items,
            source_items,
            asset_items,
            question_items,
            reference_items,
        )

        for collection in collections:
            for item in collection:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                item_id = item.get(
                    "id"
                )

                if (
                    isinstance(
                        item_id,
                        str,
                    )
                    and
                    item_id.strip()
                ):
                    values.append(
                        item_id
                    )

        for section in content_items:
            if not isinstance(
                section,
                dict,
            ):
                continue

            blocks = section.get(
                "blocos"
            )

            if not isinstance(
                blocks,
                list,
            ):
                continue

            for block in blocks:
                if not isinstance(
                    block,
                    dict,
                ):
                    continue

                block_id = block.get(
                    "id"
                )

                if (
                    isinstance(
                        block_id,
                        str,
                    )
                    and
                    block_id.strip()
                ):
                    values.append(
                        block_id
                    )

        counter = Counter(
            values
        )

        duplicates = sorted(
            value
            for value, count
            in counter.items()
            if count > 1
        )

        return [
            (
                "ID duplicado "
                "no documento: "
                f"{item_id}"
            )
            for item_id
            in duplicates
        ]

    @staticmethod
    def _validate_map_relationships(
        *,
        map_items: list[Any],
        map_ids: set[str],
    ) -> list[str]:
        """
        Valida parent_id e detecta ciclos
        hierárquicos no mapa.
        """

        errors: list[str] = []

        parents: dict[
            str,
            str | None,
        ] = {}

        for item in map_items:
            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = item.get(
                "id"
            )

            parent_id = item.get(
                "parent_id"
            )

            if not isinstance(
                item_id,
                str,
            ):
                continue

            parents[
                item_id
            ] = (
                parent_id
                if isinstance(
                    parent_id,
                    str,
                )
                else None
            )

            if parent_id is None:
                continue

            if (
                isinstance(
                    parent_id,
                    str,
                )
                and
                parent_id not in map_ids
            ):
                errors.append(
                    "mapa_estrutura: "
                    f"{item_id!r} possui "
                    "parent_id inexistente: "
                    f"{parent_id!r}"
                )

            if (
                parent_id
                == item_id
            ):
                errors.append(
                    "mapa_estrutura: "
                    f"{item_id!r} não pode "
                    "ser pai de si mesmo."
                )

        reported_cycles: set[
            tuple[str, ...]
        ] = set()

        for item_id in parents:
            path: list[str] = []

            position: dict[
                str,
                int,
            ] = {}

            current: str | None = (
                item_id
            )

            while current is not None:
                if current in position:
                    cycle = path[
                        position[current]:
                    ]

                    canonical = tuple(
                        sorted(
                            cycle
                        )
                    )

                    if (
                        canonical
                        not in reported_cycles
                    ):
                        reported_cycles.add(
                            canonical
                        )

                        errors.append(
                            "mapa_estrutura: "
                            "ciclo hierárquico "
                            "detectado envolvendo: "
                            + ", ".join(
                                repr(item)
                                for item in cycle
                            )
                        )

                    break

                position[
                    current
                ] = len(path)

                path.append(
                    current
                )

                current = parents.get(
                    current
                )

        return errors

    @staticmethod
    def _validate_summary_relationships(
        *,
        summary_items: list[Any],
        map_ids: set[str],
    ) -> list[str]:
        """
        Garante que estrutura_resumida utilize
        IDs existentes no mapa principal.
        """

        errors: list[str] = []

        seen: set[str] = set()

        for index, item in enumerate(
            summary_items
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            item_id = item.get(
                "id"
            )

            if not isinstance(
                item_id,
                str,
            ):
                continue

            if (
                item_id
                not in map_ids
            ):
                errors.append(
                    "cabecalho."
                    "estrutura_resumida"
                    f"[{index}].id aponta "
                    "para seção inexistente: "
                    f"{item_id!r}"
                )

            if item_id in seen:
                errors.append(
                    "cabecalho."
                    "estrutura_resumida "
                    "possui ID repetido: "
                    f"{item_id!r}"
                )

            seen.add(
                item_id
            )

        return errors

    @staticmethod
    def _validate_content_sections(
        *,
        content_items: list[Any],
        map_ids: set[str],
    ) -> list[str]:
        """
        Verifica as seções usadas pela coleção
        de conteúdo.
        """

        errors: list[str] = []

        seen_sections: set[
            str
        ] = set()

        for index, section in enumerate(
            content_items
        ):
            if not isinstance(
                section,
                dict,
            ):
                continue

            section_id = section.get(
                "section_id"
            )

            if not isinstance(
                section_id,
                str,
            ):
                continue

            if (
                section_id
                not in map_ids
            ):
                errors.append(
                    f"conteudo[{index}]."
                    "section_id aponta "
                    "para seção inexistente: "
                    f"{section_id!r}"
                )

            if (
                section_id
                in seen_sections
            ):
                errors.append(
                    "A seção "
                    f"{section_id!r} "
                    "aparece mais de uma vez "
                    "em conteudo."
                )

            seen_sections.add(
                section_id
            )

        return errors

    @staticmethod
    def _validate_question_answers(
        *,
        questions: list[Any],
        answers: list[Any],
    ) -> list[str]:
        """
        Valida o relacionamento entre questões
        e gabaritos.
        """

        errors: list[str] = []

        question_map: dict[
            str,
            dict[str, Any],
        ] = {}

        for question in questions:
            if not isinstance(
                question,
                dict,
            ):
                continue

            question_id = question.get(
                "id"
            )

            if isinstance(
                question_id,
                str,
            ):
                question_map[
                    question_id
                ] = question

        answer_ids: list[
            str
        ] = []

        for index, answer in enumerate(
            answers
        ):
            if not isinstance(
                answer,
                dict,
            ):
                continue

            question_id = answer.get(
                "question_id"
            )

            if not isinstance(
                question_id,
                str,
            ):
                continue

            answer_ids.append(
                question_id
            )

            if (
                question_id
                not in question_map
            ):
                errors.append(
                    f"gabaritos[{index}]."
                    "question_id aponta "
                    "para questão inexistente: "
                    f"{question_id!r}"
                )

                continue

            question = (
                question_map[
                    question_id
                ]
            )

            question_type = (
                question.get(
                    "tipo"
                )
            )

            if (
                question_type
                == "multipla_escolha"
            ):
                alternatives = (
                    question.get(
                        "alternativas"
                    )
                )

                if isinstance(
                    alternatives,
                    list,
                ):
                    alternative_ids = {
                        alternative.get(
                            "id"
                        )
                        for alternative
                        in alternatives
                        if isinstance(
                            alternative,
                            dict,
                        )
                        and isinstance(
                            alternative.get(
                                "id"
                            ),
                            str,
                        )
                    }

                    resposta = (
                        answer.get(
                            "resposta"
                        )
                    )

                    if (
                        isinstance(
                            resposta,
                            str,
                        )
                        and resposta
                        and resposta
                        not in alternative_ids
                    ):
                        errors.append(
                            "gabarito de "
                            f"{question_id!r}: "
                            "resposta "
                            f"{resposta!r} "
                            "não corresponde "
                            "a uma alternativa "
                            "existente."
                        )

        answer_counter = Counter(
            answer_ids
        )

        for (
            question_id,
            count,
        ) in answer_counter.items():
            if count > 1:
                errors.append(
                    "A questão "
                    f"{question_id!r} "
                    "possui mais de "
                    "um gabarito."
                )

        answered = set(
            answer_ids
        )

        for question_id in question_map:
            if (
                question_id
                not in answered
            ):
                errors.append(
                    "A questão "
                    f"{question_id!r} "
                    "não possui gabarito."
                )

        return errors

    def _validate_cross_references(
        self,
        *,
        document: dict[str, Any],
        map_ids: set[str],
        objective_ids: set[str],
        source_ids: set[str],
        asset_ids: set[str],
        block_ids: set[str],
        question_ids: set[str],
        reference_ids: set[str],
    ) -> list[str]:
        """
        Caminha recursivamente pelo documento
        procurando referências internas
        conhecidas.
        """

        errors: list[str] = []

        def validate_string_list(
            value: Any,
            valid_ids: set[str],
            path: str,
            label: str,
        ) -> None:
            if not isinstance(
                value,
                list,
            ):
                return

            for index, item_id in enumerate(
                value
            ):
                if (
                    isinstance(
                        item_id,
                        str,
                    )
                    and item_id
                    and item_id
                    not in valid_ids
                ):
                    errors.append(
                        f"{path}[{index}] "
                        "aponta para "
                        f"{label} inexistente: "
                        f"{item_id!r}"
                    )

        def walk(
            value: Any,
            path: str,
        ) -> None:
            if isinstance(
                value,
                dict,
            ):
                for (
                    key,
                    child,
                ) in value.items():
                    child_path = (
                        f"{path}.{key}"
                    )

                    if (
                        key
                        == "source_refs"
                    ):
                        if isinstance(
                            child,
                            list,
                        ):
                            for (
                                index,
                                ref,
                            ) in enumerate(
                                child
                            ):
                                if not isinstance(
                                    ref,
                                    dict,
                                ):
                                    continue

                                source_id = (
                                    ref.get(
                                        "source_id"
                                    )
                                )

                                if (
                                    isinstance(
                                        source_id,
                                        str,
                                    )
                                    and source_id
                                    and source_id
                                    not in source_ids
                                ):
                                    errors.append(
                                        f"{child_path}"
                                        f"[{index}]"
                                        ".source_id "
                                        "aponta para "
                                        "fonte inexistente: "
                                        f"{source_id!r}"
                                    )

                    elif (
                        key
                        == "objetivos_ids"
                    ):
                        validate_string_list(
                            child,
                            objective_ids,
                            child_path,
                            "objetivo",
                        )

                    elif key in (
                        "section_refs",
                        "revisar_section_refs",
                        "topicos_relacionados",
                    ):
                        validate_string_list(
                            child,
                            map_ids,
                            child_path,
                            "seção",
                        )

                    elif (
                        key
                        == "asset_ref"
                    ):
                        if (
                            isinstance(
                                child,
                                str,
                            )
                            and child
                            and child
                            not in asset_ids
                        ):
                            errors.append(
                                f"{child_path} "
                                "aponta para "
                                "asset inexistente: "
                                f"{child!r}"
                            )

                    elif (
                        key
                        == "recursos"
                    ):
                        validate_string_list(
                            child,
                            (
                                block_ids
                                | asset_ids
                            ),
                            child_path,
                            "recurso",
                        )

                    elif (
                        key
                        == "reference_refs"
                    ):
                        validate_string_list(
                            child,
                            reference_ids,
                            child_path,
                            "referência",
                        )

                    elif (
                        key
                        == "question_refs"
                    ):
                        validate_string_list(
                            child,
                            question_ids,
                            child_path,
                            "questão",
                        )

                    walk(
                        child,
                        child_path,
                    )

            elif isinstance(
                value,
                list,
            ):
                for (
                    index,
                    child,
                ) in enumerate(
                    value
                ):
                    walk(
                        child,
                        f"{path}[{index}]",
                    )

        walk(
            document,
            "$",
        )

        return errors

    @staticmethod
    def _deduplicate_errors(
        errors: list[str],
    ) -> list[str]:
        """
        Remove mensagens duplicadas preservando
        a ordem original.
        """

        seen: set[str] = set()

        result: list[str] = []

        for error in errors:
            if error in seen:
                continue

            seen.add(
                error
            )

            result.append(
                error
            )

        return result