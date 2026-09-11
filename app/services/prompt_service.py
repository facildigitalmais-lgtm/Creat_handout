from __future__ import annotations

import json

from pathlib import Path
from threading import RLock
from typing import Any

from app.core.settings import get_settings


class PromptService:
    """
    Serviço responsável pelos prompts utilizados
    pela aplicação.

    O prompt de conversão de apostila para JSON
    é montado dinamicamente usando:

    - o arquivo de template em prompts/;
    - o JSON Schema atualmente configurado;
    - a versão atual do contrato;
    - o document_type atual.

    Dessa forma, o prompt entregue ao usuário
    permanece sincronizado com o formato aceito
    pelo Montador de Apostilas.
    """

    SCHEMA_VERSION_TOKEN = (
        "{{SCHEMA_VERSION}}"
    )

    DOCUMENT_TYPE_TOKEN = (
        "{{DOCUMENT_TYPE}}"
    )

    JSON_SCHEMA_TOKEN = (
        "{{JSON_SCHEMA}}"
    )

    def __init__(self) -> None:
        self.settings = get_settings()

        self._lock = RLock()

        self._cached_prompt: (
            str | None
        ) = None

        self._cached_signature: (
            tuple[int, int] | None
        ) = None

    def get_converter_prompt(
        self,
    ) -> str:
        """
        Retorna o prompt completo usado para
        converter uma apostila de matéria
        para o JSON aceito pelo sistema.

        O resultado é armazenado em cache,
        mas o cache é automaticamente
        invalidado quando o template ou
        o schema forem modificados.
        """

        with self._lock:
            signature = (
                self._file_signature(
                    self.settings
                    .prompt_template_file
                ),
                self._file_signature(
                    self.settings
                    .schema_file
                ),
            )

            if (
                self._cached_prompt
                is not None
                and
                self._cached_signature
                == signature
            ):
                return (
                    self._cached_prompt
                )

            prompt = self._build_prompt()

            self._cached_prompt = prompt
            self._cached_signature = (
                signature
            )

            return prompt

    def reload(
        self,
    ) -> str:
        """
        Força a reconstrução do prompt.
        """

        with self._lock:
            self._cached_prompt = None
            self._cached_signature = None

        return self.get_converter_prompt()

    def get_metadata(
        self,
    ) -> dict[str, Any]:
        """
        Retorna informações úteis sobre
        o contrato atualmente utilizado.
        """

        schema = self._read_schema()

        return {
            "schema_version": (
                self._schema_version(
                    schema
                )
            ),
            "document_type": (
                self._document_type(
                    schema
                )
            ),
            "schema_file": str(
                self.settings
                .schema_file
            ),
            "prompt_template_file": str(
                self.settings
                .prompt_template_file
            ),
        }

    def _build_prompt(
        self,
    ) -> str:
        """
        Monta o prompt final substituindo
        os tokens do template.
        """

        template = self._read_text(
            self.settings
            .prompt_template_file
        )

        schema = self._read_schema()

        schema_version = (
            self._schema_version(
                schema
            )
        )

        document_type = (
            self._document_type(
                schema
            )
        )

        schema_text = json.dumps(
            schema,
            ensure_ascii=False,
            indent=2,
        )

        self._validate_template_tokens(
            template
        )

        prompt = template.replace(
            self.SCHEMA_VERSION_TOKEN,
            schema_version,
        )

        prompt = prompt.replace(
            self.DOCUMENT_TYPE_TOKEN,
            document_type,
        )

        prompt = prompt.replace(
            self.JSON_SCHEMA_TOKEN,
            schema_text,
        )

        return prompt

    def _read_schema(
        self,
    ) -> dict[str, Any]:
        """
        Carrega o JSON Schema configurado.
        """

        path = (
            self.settings
            .schema_file
        )

        if not path.exists():
            raise FileNotFoundError(
                "JSON Schema não "
                "encontrado: "
                f"{path}"
            )

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                schema = json.load(
                    file
                )

        except json.JSONDecodeError as error:
            raise ValueError(
                "O JSON Schema possui "
                "JSON inválido: "
                f"linha {error.lineno}, "
                f"coluna {error.colno}: "
                f"{error.msg}"
            ) from error

        except OSError as error:
            raise OSError(
                "Não foi possível ler "
                "o JSON Schema: "
                f"{path}"
            ) from error

        if not isinstance(
            schema,
            dict,
        ):
            raise ValueError(
                "O JSON Schema deve "
                "possuir um objeto "
                "JSON na raiz."
            )

        return schema

    @staticmethod
    def _read_text(
        path: Path,
    ) -> str:
        """
        Lê um arquivo de texto UTF-8.
        """

        if not path.exists():
            raise FileNotFoundError(
                "Template de prompt "
                "não encontrado: "
                f"{path}"
            )

        try:
            return path.read_text(
                encoding="utf-8"
            )

        except OSError as error:
            raise OSError(
                "Não foi possível ler "
                "o template de prompt: "
                f"{path}"
            ) from error

    @staticmethod
    def _schema_version(
        schema: dict[str, Any],
    ) -> str:
        """
        Obtém schema_version diretamente
        do contrato JSON.
        """

        value = (
            schema
            .get(
                "properties",
                {},
            )
            .get(
                "schema_version",
                {},
            )
            .get(
                "const"
            )
        )

        if not isinstance(
            value,
            str,
        ) or not value:
            raise ValueError(
                "O JSON Schema não "
                "declara "
                "properties."
                "schema_version.const."
            )

        return value

    @staticmethod
    def _document_type(
        schema: dict[str, Any],
    ) -> str:
        """
        Obtém document_type diretamente
        do contrato JSON.
        """

        value = (
            schema
            .get(
                "properties",
                {},
            )
            .get(
                "document_type",
                {},
            )
            .get(
                "const"
            )
        )

        if not isinstance(
            value,
            str,
        ) or not value:
            raise ValueError(
                "O JSON Schema não "
                "declara "
                "properties."
                "document_type.const."
            )

        return value

    @classmethod
    def _validate_template_tokens(
        cls,
        template: str,
    ) -> None:
        """
        Garante que o template possua
        todos os marcadores necessários.
        """

        required_tokens = (
            cls.SCHEMA_VERSION_TOKEN,
            cls.DOCUMENT_TYPE_TOKEN,
            cls.JSON_SCHEMA_TOKEN,
        )

        missing = [
            token
            for token
            in required_tokens
            if token not in template
        ]

        if missing:
            raise ValueError(
                "O template do prompt "
                "não possui todos os "
                "marcadores obrigatórios: "
                + ", ".join(
                    missing
                )
            )

    @staticmethod
    def _file_signature(
        path: Path,
    ) -> int:
        """
        Retorna uma assinatura simples baseada
        no timestamp de modificação do arquivo.

        É suficiente para invalidar o cache
        durante o desenvolvimento.
        """

        if not path.exists():
            raise FileNotFoundError(
                "Arquivo necessário "
                "não encontrado: "
                f"{path}"
            )

        return (
            path.stat()
            .st_mtime_ns
        )


prompt_service = PromptService()