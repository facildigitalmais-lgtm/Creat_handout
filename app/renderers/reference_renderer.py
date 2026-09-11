from __future__ import annotations

from typing import Any


class ReferenceRenderer:
    """
    Normaliza referências e calcula uma chave
    semântica para consolidação.
    """

    def normalize(
        self,
        reference: dict[str, Any],
    ) -> dict[str, Any]:
        authors = reference.get(
            "autor"
        )

        if not isinstance(
            authors,
            list,
        ):
            authors = []

        return {
            "id": reference.get("id"),
            "ordem": reference.get(
                "ordem",
                0,
            ),
            "tipo": reference.get(
                "tipo"
            ),
            "autor": [
                str(author)
                for author in authors
            ],
            "autor_entidade": (
                reference.get(
                    "autor_entidade"
                )
            ),
            "titulo": str(
                reference.get(
                    "titulo"
                )
                or ""
            ),
            "subtitulo": (
                reference.get(
                    "subtitulo"
                )
            ),
            "edicao": (
                reference.get(
                    "edicao"
                )
            ),
            "local": (
                reference.get(
                    "local"
                )
            ),
            "editora": (
                reference.get(
                    "editora"
                )
            ),
            "ano": (
                reference.get(
                    "ano"
                )
            ),
            "doi": (
                reference.get(
                    "doi"
                )
            ),
            "url": (
                reference.get(
                    "url"
                )
            ),
            "data_acesso": (
                reference.get(
                    "data_acesso"
                )
            ),
            "norma_abnt_formatada": (
                reference.get(
                    "norma_abnt_formatada"
                )
            ),
        }

    def deduplication_key(
        self,
        reference: dict[str, Any],
    ) -> str:
        normalized = self.normalize(
            reference
        )

        ready = (
            normalized.get(
                "norma_abnt_formatada"
            )
        )

        if isinstance(
            ready,
            str,
        ) and ready.strip():
            return self._normalize_text(
                ready
            )

        authors = ";".join(
            normalized.get(
                "autor"
            )
            or []
        )

        parts = (
            authors,
            str(
                normalized.get(
                    "autor_entidade"
                )
                or ""
            ),
            str(
                normalized.get(
                    "titulo"
                )
                or ""
            ),
            str(
                normalized.get(
                    "ano"
                )
                or ""
            ),
            str(
                normalized.get(
                    "doi"
                )
                or ""
            ),
            str(
                normalized.get(
                    "url"
                )
                or ""
            ),
        )

        return "|".join(
            self._normalize_text(
                part
            )
            for part in parts
        )

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        return " ".join(
            str(value)
            .strip()
            .casefold()
            .split()
        )


reference_renderer = ReferenceRenderer()