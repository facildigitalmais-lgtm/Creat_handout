"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const reloadButton = document.querySelector(
        "#reload-library"
    );

    const statusElement = document.querySelector(
        "#reload-status"
    );

    if (!reloadButton) {
        return;
    }

    reloadButton.addEventListener(
        "click",
        async () => {
            reloadButton.disabled = true;
            reloadButton.textContent = "Recarregando...";

            if (statusElement) {
                statusElement.textContent =
                    "Lendo e validando os arquivos JSON...";

                statusElement.classList.remove(
                    "status-message--success",
                    "status-message--error"
                );
            }

            try {
                const response = await fetch(
                    "/api/catalogo/recarregar",
                    {
                        method: "POST",
                        headers: {
                            "Accept": "application/json"
                        }
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `HTTP ${response.status}`
                    );
                }

                const data = await response.json();

                if (statusElement) {
                    const stats =
                        data.catalogo.estatisticas;

                    statusElement.textContent =
                        `${stats.validos} módulo(s) válido(s), ` +
                        `${stats.invalidos} inválido(s).`;

                    statusElement.classList.add(
                        "status-message--success"
                    );
                }

                window.setTimeout(
                    () => {
                        window.location.reload();
                    },
                    500
                );
            } catch (error) {
                console.error(error);

                if (statusElement) {
                    statusElement.textContent =
                        "Não foi possível recarregar a biblioteca.";

                    statusElement.classList.add(
                        "status-message--error"
                    );
                }
            } finally {
                reloadButton.disabled = false;
                reloadButton.textContent =
                    "Recarregar biblioteca";
            }
        }
    );
});