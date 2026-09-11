from __future__ import annotations

from copy import deepcopy
from typing import Any


BOX_TYPES = {
    "conceito_chave": {
        "label": "Conceito-chave",
        "class_name": "concept",
    },
    "definicao": {
        "label": "Definição",
        "class_name": "definition",
    },
    "observacao": {
        "label": "Observação",
        "class_name": "observation",
    },
    "atencao": {
        "label": "Atenção",
        "class_name": "attention",
    },
    "cuidado": {
        "label": "Cuidado",
        "class_name": "danger",
    },
    "erro_comum": {
        "label": "Erro comum",
        "class_name": "danger",
    },
    "para_memorizar": {
        "label": "Para memorizar",
        "class_name": "memorize",
    },
    "raciocinio": {
        "label": "Raciocínio",
        "class_name": "reasoning",
    },
    "exemplo": {
        "label": "Exemplo",
        "class_name": "example",
    },
    "contraexemplo": {
        "label": "Contraexemplo",
        "class_name": "example",
    },
    "exemplo_resolvido": {
        "label": "Exemplo resolvido",
        "class_name": "example",
    },
    "estudo_de_caso": {
        "label": "Estudo de caso",
        "class_name": "case-study",
    },
    "analise_guiada": {
        "label": "Análise guiada",
        "class_name": "reasoning",
    },
    "micropratica": {
        "label": "Pratique",
        "class_name": "practice",
    },
}


class BlockRenderer:
    """
    Converte blocos heterogêneos do JSON da matéria
    para uma representação editorial previsível.

    O serviço não produz HTML diretamente.

    Ele normaliza os dados para que os templates
    Jinja sejam simples, seguros e independentes
    da matéria estudada.
    """

    def normalize(
        self,
        block: dict[str, Any],
        *,
        assets_by_id: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        assets_by_id = assets_by_id or {}

        block_type = str(
            block.get("tipo")
            or "paragrafo"
        ).strip()

        content = block.get("conteudo")

        if not isinstance(content, dict):
            content = {
                "texto": (
                    ""
                    if content is None
                    else str(content)
                )
            }

        result: dict[str, Any] = {
            "id": block.get("id"),
            "ordem": block.get("ordem", 0),
            "tipo": block_type,
            "visibilidade": block.get(
                "visibilidade",
                "aluno",
            ),
            "tags": (
                block.get("tags")
                if isinstance(
                    block.get("tags"),
                    list,
                )
                else []
            ),
            "render_hint": (
                deepcopy(
                    block.get("render_hint")
                )
                if isinstance(
                    block.get("render_hint"),
                    dict,
                )
                else {}
            ),
            "raw": deepcopy(content),
        }

        if block_type in {
            "titulo",
            "subtitulo",
            "paragrafo",
            "legenda",
            "citacao",
        }:
            result.update(
                self._normalize_text_block(
                    content
                )
            )

            return result

        if block_type in BOX_TYPES:
            result.update(
                self._normalize_box(
                    block_type,
                    content,
                )
            )

            return result

        if block_type == "lista":
            result.update(
                self._normalize_list(
                    content
                )
            )

            return result

        if block_type == "tabela":
            result.update(
                self._normalize_table(
                    content
                )
            )

            return result

        if block_type in {
            "formula",
            "equacao",
        }:
            result.update(
                self._normalize_formula(
                    content
                )
            )

            return result

        if block_type == "codigo":
            result.update(
                self._normalize_code(
                    content
                )
            )

            return result

        if block_type in {
            "imagem",
            "figura",
            "grafico",
            "mapa",
            "diagrama",
            "fluxograma",
            "linha_do_tempo",
            "mecanismo",
        }:
            result.update(
                self._normalize_visual(
                    content,
                    assets_by_id,
                )
            )

            return result

        if block_type == "separador_logico":
            result["template_kind"] = (
                "separator"
            )

            return result

        if block_type == "comentario_editorial":
            result.update(
                self._normalize_text_block(
                    content
                )
            )

            result["template_kind"] = (
                "editorial"
            )

            return result

        result.update(
            self._normalize_generic(
                content
            )
        )

        return result

    def _normalize_text_block(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "template_kind": "text",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "texto": self._first_text(
                content,
                (
                    "texto",
                    "descricao",
                    "conteudo",
                    "valor",
                ),
            ),
        }

    def _normalize_box(
        self,
        block_type: str,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        config = BOX_TYPES[
            block_type
        ]

        details = self._remaining_fields(
            content,
            {
                "titulo",
                "rotulo",
                "texto",
                "descricao",
                "conteudo",
                "valor",
            },
        )

        return {
            "template_kind": "box",
            "box_label": (
                self._first_text(
                    content,
                    (
                        "titulo",
                        "rotulo",
                    ),
                )
                or config["label"]
            ),
            "box_class": config[
                "class_name"
            ],
            "texto": self._first_text(
                content,
                (
                    "texto",
                    "descricao",
                    "conteudo",
                    "valor",
                ),
            ),
            "detalhes": details,
        }

    def _normalize_list(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        raw_items = (
            content.get("itens")
            or content.get("items")
            or content.get("lista")
            or []
        )

        if not isinstance(
            raw_items,
            list,
        ):
            raw_items = [
                raw_items
            ]

        items = [
            self._stringify_value(
                item
            )
            for item in raw_items
        ]

        list_type = str(
            content.get("tipo_lista")
            or content.get("estilo")
            or "unordered"
        ).lower()

        ordered = list_type in {
            "ordered",
            "ordenada",
            "numerada",
            "ol",
        }

        return {
            "template_kind": "list",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "itens": items,
            "ordenada": ordered,
        }

    def _normalize_table(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        headers = (
            content.get("colunas")
            or content.get("cabecalho")
            or content.get("headers")
            or []
        )

        rows = (
            content.get("linhas")
            or content.get("rows")
            or []
        )

        if not isinstance(
            headers,
            list,
        ):
            headers = [
                headers
            ]

        normalized_headers = [
            self._stringify_value(
                item
            )
            for item in headers
        ]

        normalized_rows: list[
            list[str]
        ] = []

        if isinstance(
            rows,
            list,
        ):
            for row in rows:
                if isinstance(
                    row,
                    dict,
                ):
                    if normalized_headers:
                        normalized_rows.append(
                            [
                                self._stringify_value(
                                    row.get(
                                        header,
                                        "",
                                    )
                                )
                                for header
                                in normalized_headers
                            ]
                        )

                    else:
                        if not normalized_headers:
                            normalized_headers = [
                                str(key)
                                for key
                                in row.keys()
                            ]

                        normalized_rows.append(
                            [
                                self._stringify_value(
                                    row.get(
                                        key,
                                        "",
                                    )
                                )
                                for key
                                in row.keys()
                            ]
                        )

                elif isinstance(
                    row,
                    list,
                ):
                    normalized_rows.append(
                        [
                            self._stringify_value(
                                cell
                            )
                            for cell in row
                        ]
                    )

                else:
                    normalized_rows.append(
                        [
                            self._stringify_value(
                                row
                            )
                        ]
                    )

        return {
            "template_kind": "table",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "cabecalho": normalized_headers,
            "linhas": normalized_rows,
            "nota": self._first_text(
                content,
                (
                    "nota",
                    "observacao",
                    "fonte",
                ),
            ),
        }

    def _normalize_formula(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        variables = (
            content.get("variaveis")
            or []
        )

        if isinstance(
            variables,
            dict,
        ):
            variables = [
                {
                    "simbolo": key,
                    "descricao": (
                        self._stringify_value(
                            value
                        )
                    ),
                }
                for key, value
                in variables.items()
            ]

        elif not isinstance(
            variables,
            list,
        ):
            variables = []

        return {
            "template_kind": "formula",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "latex": self._first_text(
                content,
                (
                    "latex",
                    "formula",
                    "equacao",
                ),
            ),
            "texto_linear": (
                self._first_text(
                    content,
                    (
                        "texto_linear",
                        "texto",
                        "expressao",
                    ),
                )
            ),
            "descricao": self._first_text(
                content,
                (
                    "descricao",
                    "explicacao",
                ),
            ),
            "variaveis": variables,
            "unidades": self._first_text(
                content,
                (
                    "unidades",
                    "unidade",
                ),
            ),
        }

    def _normalize_code(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "template_kind": "code",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "linguagem": self._first_text(
                content,
                (
                    "linguagem",
                    "language",
                ),
            ),
            "codigo": self._first_text(
                content,
                (
                    "codigo",
                    "code",
                    "texto",
                    "conteudo",
                ),
            ),
        }

    def _normalize_visual(
        self,
        content: dict[str, Any],
        assets_by_id: dict[
            str,
            dict[str, Any],
        ],
    ) -> dict[str, Any]:
        asset_ref = (
            content.get(
                "asset_ref"
            )
        )

        asset: dict[str, Any] = {}

        if (
            isinstance(
                asset_ref,
                str,
            )
            and asset_ref
            in assets_by_id
        ):
            asset = deepcopy(
                assets_by_id[
                    asset_ref
                ]
            )

        return {
            "template_kind": "visual",
            "titulo": (
                self._first_text(
                    content,
                    (
                        "titulo",
                        "rotulo",
                    ),
                )
                or self._first_text(
                    asset,
                    (
                        "titulo",
                    ),
                )
            ),
            "asset_ref": asset_ref,
            "arquivo": (
                content.get(
                    "arquivo"
                )
                or asset.get(
                    "arquivo"
                )
            ),
            "texto_alternativo": (
                self._first_text(
                    content,
                    (
                        "texto_alternativo",
                        "alt",
                    ),
                )
                or self._first_text(
                    asset,
                    (
                        "texto_alternativo",
                    ),
                )
            ),
            "descricao_visual": (
                self._first_text(
                    content,
                    (
                        "descricao_visual",
                        "descricao",
                    ),
                )
                or self._first_text(
                    asset,
                    (
                        "descricao_visual",
                    ),
                )
            ),
            "source_locator": (
                content.get(
                    "source_locator"
                )
                or asset.get(
                    "source_locator"
                )
            ),
            "required": bool(
                content.get(
                    "required",
                    asset.get(
                        "required",
                        False,
                    ),
                )
            ),
        }

    def _normalize_generic(
        self,
        content: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "template_kind": "generic",
            "titulo": self._first_text(
                content,
                (
                    "titulo",
                    "rotulo",
                ),
            ),
            "texto": self._first_text(
                content,
                (
                    "texto",
                    "descricao",
                    "conteudo",
                    "valor",
                ),
            ),
            "detalhes": (
                self._remaining_fields(
                    content,
                    {
                        "titulo",
                        "rotulo",
                        "texto",
                        "descricao",
                        "conteudo",
                        "valor",
                    },
                )
            ),
        }

    def _remaining_fields(
        self,
        content: dict[str, Any],
        ignored: set[str],
    ) -> list[dict[str, str]]:
        details: list[
            dict[str, str]
        ] = []

        for key, value in content.items():
            if key in ignored:
                continue

            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            details.append(
                {
                    "label": (
                        str(key)
                        .replace("_", " ")
                        .strip()
                        .capitalize()
                    ),
                    "value": (
                        self._stringify_value(
                            value
                        )
                    ),
                }
            )

        return details

    def _first_text(
        self,
        content: dict[str, Any],
        keys: tuple[str, ...],
    ) -> str:
        for key in keys:
            value = content.get(
                key
            )

            if value in (
                None,
                "",
                [],
                {},
            ):
                continue

            return self._stringify_value(
                value
            )

        return ""

    def _stringify_value(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        if isinstance(
            value,
            bool,
        ):
            return (
                "Sim"
                if value
                else "Não"
            )

        if isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            return str(value)

        if isinstance(
            value,
            list,
        ):
            return "; ".join(
                self._stringify_value(
                    item
                )
                for item in value
                if item not in (
                    None,
                    "",
                )
            )

        if isinstance(
            value,
            dict,
        ):
            return "; ".join(
                (
                    f"{str(key).replace('_', ' ')}: "
                    f"{self._stringify_value(item)}"
                )
                for key, item
                in value.items()
                if item not in (
                    None,
                    "",
                    [],
                    {},
                )
            )

        return str(value)


block_renderer = BlockRenderer()