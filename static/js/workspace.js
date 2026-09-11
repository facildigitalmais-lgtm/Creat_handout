"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const state = {
        currentStep: 1,
        totalSteps: 5,
        selectedSubjects: [],
        coverUrl: null,
        coverUrlIsObject: false,
        coverFile: null,
        coverRemoved: false,
        projectId: null,
        projectUpdatedAt: null,
        pdfAudit: null,
        promptText: "",
    };

    const STORAGE_KEY = "facildigital_apostila_draft_v1";

    const form = document.querySelector("#project-form");

    const stepSections = Array.from(
        document.querySelectorAll(".workspace-step")
    );

    const stepButtons = Array.from(
        document.querySelectorAll("[data-step-target]")
    );

    const previousButton = document.querySelector("#previous-step");
    const nextButton = document.querySelector("#next-step");
    const stepIndicator = document.querySelector("#step-indicator");

    const reloadButton = document.querySelector("#reload-library");

    const newProjectButton = document.querySelector("#new-project-button");
    const openProjectsButton = document.querySelector(
        "#open-projects-button"
    );

    const saveProjectButton = document.querySelector(
        "#save-project-button"
    );

    const draftStatus = document.querySelector("#draft-status");

    const projectsModal = document.querySelector("#projects-modal");
    const projectsList = document.querySelector("#projects-list");
    const projectsTotal = document.querySelector("#projects-total");
    const closeProjectsModal = document.querySelector(
        "#close-projects-modal"
    );

    const refreshProjectsButton = document.querySelector(
        "#refresh-projects-button"
    );

    const projectsNewButton = document.querySelector(
        "#projects-new-button"
    );

    const promptButton = document.querySelector("#copy-prompt-button");
    const promptModal = document.querySelector("#prompt-modal");
    const promptTextArea = document.querySelector("#prompt-text");
    const promptSize = document.querySelector("#prompt-size");
    const closePromptModal = document.querySelector("#close-prompt-modal");
    const modalCopyPrompt = document.querySelector("#modal-copy-prompt");
    const selectPromptButton = document.querySelector("#select-prompt-button");

    const toastRegion = document.querySelector("#toast-region");

    const coverInput = document.querySelector("#cover-input");
    const selectCoverButton = document.querySelector("#select-cover-button");
    const removeCoverButton = document.querySelector("#remove-cover-button");
    const coverDropzone = document.querySelector("#cover-dropzone");
    const coverPreview = document.querySelector("#cover-preview");
    const coverPreviewImage = document.querySelector("#cover-preview-image");
    const coverPreviewEmpty = document.querySelector("#cover-preview-empty");
    const coverFileInfo = document.querySelector("#cover-file-info");
    const coverFileName = document.querySelector("#cover-file-name");
    const coverFileSize = document.querySelector("#cover-file-size");

    const subjectSearch = document.querySelector("#subject-search");
    const subjectCards = Array.from(
        document.querySelectorAll(".subject-card")
    );

    const subjectCheckboxes = Array.from(
        document.querySelectorAll(".subject-checkbox")
    );

    const selectAllSubjects = document.querySelector(
        "#select-all-subjects"
    );

    const clearSubjects = document.querySelector("#clear-subjects");

    const selectedContainer = document.querySelector(
        "#selected-subjects"
    );

    const selectedEmpty = document.querySelector("#selected-empty");

    const selectedCount = document.querySelector("#selected-count");
    const selectedCountHeading = document.querySelector(
        "#selected-count-heading"
    );

    const reviewTitle = document.querySelector("#review-title");
    const reviewSubtitle = document.querySelector("#review-subtitle");
    const reviewBank = document.querySelector("#review-bank");
    const reviewYear = document.querySelector("#review-year");
    const reviewCover = document.querySelector("#review-cover");
    const reviewSubjectCount = document.querySelector(
        "#review-subject-count"
    );

    const reviewSubjectList = document.querySelector(
        "#review-subject-list"
    );

    const reviewExercises = document.querySelector("#review-exercises");
    const reviewAnswers = document.querySelector("#review-answers");
    const reviewReferences = document.querySelector("#review-references");
    const reviewNewPage = document.querySelector("#review-new-page");

    const generatePreviewButton = document.querySelector(
        "#generate-preview-button"
    );

    const openPdfButton = document.querySelector(
        "#open-pdf-button"
    );

    const downloadPdfButton = document.querySelector(
        "#download-pdf-button"
    );

    const pdfStatus = document.querySelector(
        "#pdf-status"
    );

    const openAuditButton = document.querySelector(
        "#open-audit-button"
    );

    const auditModal = document.querySelector(
        "#audit-modal"
    );

    const closeAuditModal = document.querySelector(
        "#close-audit-modal"
    );

    const auditSummary = document.querySelector(
        "#audit-summary"
    );

    const auditGrid = document.querySelector(
        "#audit-grid"
    );

    const auditFooterStatus = document.querySelector(
        "#audit-footer-status"
    );

    const reauditPdfButton = document.querySelector(
        "#reaudit-pdf-button"
    );

    const auditOpenPdfButton = document.querySelector(
        "#audit-open-pdf-button"
    );

    const auditFilterButtons = Array.from(
        document.querySelectorAll(
            "[data-audit-filter]"
        )
    );

    let draggedItem = null;

    function showToast(message, type = "success") {
        const toast = document.createElement("div");

        toast.className = `toast toast--${type}`;

        const dot = document.createElement("span");
        dot.className = "toast__dot";

        const text = document.createElement("span");
        text.textContent = message;

        toast.append(dot, text);
        toastRegion.appendChild(toast);

        window.setTimeout(() => {
            toast.remove();
        }, 3600);
    }

    function getFieldValue(name) {
        const field = form.elements.namedItem(name);

        if (!field) {
            return "";
        }

        if (field instanceof RadioNodeList) {
            return field.value;
        }

        if (field.type === "checkbox") {
            return field.checked;
        }

        return field.value ?? "";
    }

    function setFieldValue(name, value) {
        const field = form.elements.namedItem(name);

        if (!field) {
            return;
        }

        if (field instanceof RadioNodeList) {
            const radio = Array.from(field).find(
                (item) => item.value === value
            );

            if (radio) {
                radio.checked = true;
            }

            return;
        }

        if (field.type === "checkbox") {
            field.checked = Boolean(value);
            return;
        }

        if (typeof value === "string" || typeof value === "number") {
            field.value = value;
        }
    }

    function serializeForm() {
        return {
            titulo: getFieldValue("titulo"),
            concurso: getFieldValue("concurso"),
            orgao: getFieldValue("orgao"),
            banca: getFieldValue("banca"),
            cargo: getFieldValue("cargo"),
            ano: getFieldValue("ano"),
            edicao: getFieldValue("edicao"),
            editora: getFieldValue("editora"),
            site: getFieldValue("site"),
            pagina_rosto: getFieldValue("pagina_rosto"),
            aviso_legal: getFieldValue("aviso_legal"),
            cover_mode: getFieldValue("cover_mode"),
            exercises_position: getFieldValue("exercises_position"),
            answers_position: getFieldValue("answers_position"),
            references_position: getFieldValue("references_position"),
            subject_new_page: getFieldValue("subject_new_page"),
            toc_level_2: getFieldValue("toc_level_2"),
            toc_level_3: getFieldValue("toc_level_3"),
            toc_level_4: getFieldValue("toc_level_4"),
        };
    }

    function saveDraft() {
        const payload = {
            projectId: state.projectId,
            projectUpdatedAt: state.projectUpdatedAt,
            form: serializeForm(),
            selectedSubjects: state.selectedSubjects,
        };

        try {
            window.localStorage.setItem(
                STORAGE_KEY,
                JSON.stringify(payload)
            );
        } catch (error) {
            console.warn("Não foi possível salvar o rascunho.", error);
        }
    }

    function restoreDraft() {
        let draft = null;

        try {
            const raw = window.localStorage.getItem(STORAGE_KEY);

            if (raw) {
                draft = JSON.parse(raw);
            }
        } catch (error) {
            console.warn("Rascunho local inválido.", error);
        }

        if (!draft || typeof draft !== "object") {
            return;
        }

        if (
            typeof draft.projectId === "string" &&
            draft.projectId
        ) {
            state.projectId = draft.projectId;
        }

        if (
            typeof draft.projectUpdatedAt === "string" &&
            draft.projectUpdatedAt
        ) {
            state.projectUpdatedAt = draft.projectUpdatedAt;
        }

        if (draft.form && typeof draft.form === "object") {
            Object.entries(draft.form).forEach(([key, value]) => {
                setFieldValue(key, value);
            });
        }

        if (Array.isArray(draft.selectedSubjects)) {
            const validIds = new Set(
                subjectCheckboxes
                    .filter((checkbox) => !checkbox.disabled)
                    .map((checkbox) => checkbox.value)
            );

            state.selectedSubjects = draft.selectedSubjects.filter(
                (item) => validIds.has(item.id)
            );

            const selectedIds = new Set(
                state.selectedSubjects.map((item) => item.id)
            );

            subjectCheckboxes.forEach((checkbox) => {
                checkbox.checked = selectedIds.has(checkbox.value);
            });
        }

        updateSubjectCards();
        renderSelectedSubjects();

        if (state.projectId) {
            markDirty(
                "Rascunho recuperado"
            );
        }
    }

    function markDirty(label = "Alterações não salvas") {
        if (!draftStatus) {
            return;
        }

        draftStatus.textContent = label;

        draftStatus.classList.remove(
            "is-saved"
        );

        draftStatus.classList.add(
            "is-dirty"
        );
    }

    function markSaved() {
        if (!draftStatus) {
            return;
        }

        draftStatus.textContent =
            "Projeto salvo";

        draftStatus.classList.remove(
            "is-dirty"
        );

        draftStatus.classList.add(
            "is-saved"
        );
    }

    function goToStep(stepNumber) {
        const step = Math.min(
            Math.max(Number(stepNumber), 1),
            state.totalSteps
        );

        state.currentStep = step;

        stepSections.forEach((section) => {
            const isActive = Number(section.dataset.step) === step;

            section.classList.toggle("is-active", isActive);
            section.hidden = !isActive;
        });

        stepButtons.forEach((button) => {
            const target = Number(button.dataset.stepTarget);

            button.classList.toggle("is-active", target === step);
            button.classList.toggle("is-complete", target < step);
        });

        previousButton.hidden = step === 1;

        if (step === state.totalSteps) {
            nextButton.hidden = true;
            updateReview();
        } else {
            nextButton.hidden = false;
            nextButton.innerHTML = `
                Continuar
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m9 6 6 6-6 6"></path>
                </svg>
            `;
        }

        stepIndicator.textContent =
            `Etapa ${step} de ${state.totalSteps}`;

        window.scrollTo({
            top: 0,
            behavior: "smooth",
        });
    }

    function validateCurrentStep() {
        if (state.currentStep === 1) {
            const requiredFields = [
                document.querySelector("#titulo"),
                document.querySelector("#cargo"),
            ];

            const invalid = requiredFields.find(
                (field) => !field.value.trim()
            );

            if (invalid) {
                invalid.focus();

                showToast(
                    "Preencha os campos obrigatórios antes de continuar.",
                    "error"
                );

                return false;
            }
        }

        if (
            state.currentStep === 3 &&
            state.selectedSubjects.length === 0
        ) {
            showToast(
                "Selecione pelo menos uma matéria para a apostila.",
                "error"
            );

            return false;
        }

        return true;
    }

    stepButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const target = Number(button.dataset.stepTarget);

            if (
                target > state.currentStep &&
                !validateCurrentStep()
            ) {
                return;
            }

            goToStep(target);
        });
    });

    nextButton.addEventListener("click", () => {
        if (!validateCurrentStep()) {
            return;
        }

        saveDraft();
        goToStep(state.currentStep + 1);
    });

    previousButton.addEventListener("click", () => {
        saveDraft();
        goToStep(state.currentStep - 1);
    });

    form.addEventListener("input", () => {
        markDirty();
        saveDraft();
    });

    form.addEventListener("change", () => {
        markDirty();
        saveDraft();
    });

    async function reloadLibrary() {
        const originalText = reloadButton.innerHTML;

        reloadButton.disabled = true;

        reloadButton.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M20 11a8.1 8.1 0 0 0-14.7-4.7L3 9"></path>
                <path d="M3 4v5h5"></path>
                <path d="M4 13a8.1 8.1 0 0 0 14.7 4.7L21 15"></path>
                <path d="M21 20v-5h-5"></path>
            </svg>
            <span>Recarregando...</span>
        `;

        try {
            const response = await fetch(
                "/api/catalogo/recarregar",
                {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            const stats = data.catalogo.estatisticas;

            showToast(
                `Biblioteca atualizada: ${stats.validos} válida(s), ` +
                `${stats.invalidos} com erro(s).`
            );

            window.setTimeout(() => {
                window.location.reload();
            }, 600);
        } catch (error) {
            console.error(error);

            showToast(
                "Não foi possível recarregar a biblioteca.",
                "error"
            );

            reloadButton.disabled = false;
            reloadButton.innerHTML = originalText;
        }
    }

    reloadButton.addEventListener("click", reloadLibrary);

    function projectPayload() {
        const yearValue = getFieldValue("ano")
            .trim();

        return {
            project_id: state.projectId,
            dados: {
                titulo: getFieldValue("titulo").trim(),
                concurso: getFieldValue("concurso").trim(),
                orgao: getFieldValue("orgao").trim(),
                banca: getFieldValue("banca").trim(),
                cargo: getFieldValue("cargo").trim(),
                ano: yearValue || null,
                edicao: getFieldValue("edicao").trim(),
                editora: getFieldValue("editora").trim(),
                site: getFieldValue("site").trim(),
                pagina_rosto: getFieldValue("pagina_rosto"),
                aviso_legal: getFieldValue("aviso_legal"),
            },
            materias: state.selectedSubjects.map(
                (subject, index) => ({
                    id_materia: subject.id,
                    ordem: index + 1,
                    materia: subject.nome || null,
                    codigo_materia: subject.codigo || null,
                })
            ),
            editorial: {
                cover_mode: getFieldValue("cover_mode"),
                exercises_position: getFieldValue(
                    "exercises_position"
                ),
                answers_position: getFieldValue(
                    "answers_position"
                ),
                references_position: getFieldValue(
                    "references_position"
                ),
                subject_new_page: Boolean(
                    getFieldValue("subject_new_page")
                ),
                toc_level_2: Boolean(
                    getFieldValue("toc_level_2")
                ),
                toc_level_3: Boolean(
                    getFieldValue("toc_level_3")
                ),
                toc_level_4: Boolean(
                    getFieldValue("toc_level_4")
                ),
            },
        };
    }

    async function responseError(response) {
        try {
            const data = await response.json();

            if (typeof data.detail === "string") {
                return data.detail;
            }

            if (Array.isArray(data.detail)) {
                return data.detail
                    .map((item) => item.msg || "Erro de validação")
                    .join("; ");
            }

            return data.mensagem || "Erro desconhecido.";
        } catch (error) {
            return `HTTP ${response.status}`;
        }
    }

    async function uploadProjectCover(projectId) {
        if (!state.coverFile) {
            return null;
        }

        const formData = new FormData();

        formData.append(
            "file",
            state.coverFile,
            state.coverFile.name
        );

        const response = await fetch(
            `/api/projetos/${projectId}/capa`,
            {
                method: "POST",
                body: formData,
            }
        );

        if (!response.ok) {
            throw new Error(
                await responseError(response)
            );
        }

        const data = await response.json();

        return data.projeto;
    }

    async function deleteProjectCover(projectId) {
        const response = await fetch(
            `/api/projetos/${projectId}/capa`,
            {
                method: "DELETE",
                headers: {
                    Accept: "application/json",
                },
            }
        );

        if (
            !response.ok &&
            response.status !== 404
        ) {
            throw new Error(
                await responseError(response)
            );
        }

        if (response.ok) {
            const data = await response.json();

            return data.projeto;
        }

        return null;
    }

    function applyRemoteCover(project) {
        releaseCoverUrl();

        state.coverFile = null;
        state.coverRemoved = false;

        if (!project.cover_url) {
            clearCoverPreview(false);
            return;
        }

        const cacheToken = encodeURIComponent(
            project.updated_at || Date.now()
        );

        state.coverUrl =
            `${project.cover_url}?v=${cacheToken}`;

        state.coverUrlIsObject = false;

        coverPreviewImage.src = state.coverUrl;
        coverPreviewImage.hidden = false;
        coverPreviewEmpty.hidden = true;
        coverFileInfo.hidden = false;
        removeCoverButton.hidden = false;

        const cover = project.capa || {};

        coverFileName.textContent =
            cover.nome_original ||
            cover.arquivo ||
            "Capa salva";

        coverFileSize.textContent =
            formatBytes(
                Number(
                    cover.tamanho_bytes || 0
                )
            );

        updateReview();
    }

    async function saveProject() {
        const title = getFieldValue("titulo")
            .trim();

        if (!title) {
            goToStep(1);

            document
                .querySelector("#titulo")
                .focus();

            showToast(
                "Informe o nome da apostila antes de salvar.",
                "error"
            );

            return;
        }

        saveProjectButton.disabled = true;

        const originalContent =
            saveProjectButton.innerHTML;

        saveProjectButton.innerHTML = `
            <span>Salvando...</span>
        `;

        try {
            const response = await fetch(
                "/api/projetos",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Accept: "application/json",
                    },
                    body: JSON.stringify(
                        projectPayload()
                    ),
                }
            );

            if (!response.ok) {
                throw new Error(
                    await responseError(response)
                );
            }

            let data = await response.json();

            let project = data.projeto;

            state.projectId =
                project.project_id;

            if (state.coverRemoved) {
                const updatedProject =
                    await deleteProjectCover(
                        state.projectId
                    );

                if (updatedProject) {
                    project =
                        updatedProject;
                }
            }

            if (state.coverFile) {
                const updatedProject =
                    await uploadProjectCover(
                        state.projectId
                    );

                if (updatedProject) {
                    project =
                        updatedProject;
                }
            }

            state.projectUpdatedAt =
                project.updated_at;

            applyRemoteCover(project);

            state.coverFile = null;
            state.coverRemoved = false;

            updatePdfControls(
                project
            );

            saveDraft();
            markSaved();

            showToast(
                "Projeto salvo com sucesso."
            );

            updateReview();

            return project;

        } catch (error) {
            console.error(error);

            showToast(
                error.message ||
                "Não foi possível salvar o projeto.",
                "error"
            );

            return null;

        } finally {
            saveProjectButton.disabled = false;
            saveProjectButton.innerHTML =
                originalContent;
        }
    }

    function formatProjectDate(value) {
        if (!value) {
            return "Data indisponível";
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleString(
            "pt-BR",
            {
                dateStyle: "short",
                timeStyle: "short",
            }
        );
    }

    function closeProjects() {
        projectsModal.hidden = true;
        document.body.style.overflow = "";
    }

    async function loadProjects() {
        projectsList.innerHTML = `
            <div class="projects-loading">
                Carregando projetos...
            </div>
        `;

        try {
            const response = await fetch(
                "/api/projetos",
                {
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    await responseError(response)
                );
            }

            const data = await response.json();

            renderProjects(
                data.projetos || []
            );

        } catch (error) {
            console.error(error);

            projectsList.innerHTML = `
                <div class="projects-empty">
                    Não foi possível carregar os projetos.
                </div>
            `;

            projectsTotal.textContent =
                "Erro ao carregar";
        }
    }

    function renderProjects(projects) {
        projectsList.innerHTML = "";

        projectsTotal.textContent =
            `${projects.length} projeto` +
            `${projects.length === 1 ? "" : "s"}`;

        if (projects.length === 0) {
            projectsList.innerHTML = `
                <div class="projects-empty">
                    Nenhum projeto salvo ainda.
                </div>
            `;

            return;
        }

        projects.forEach((project) => {
            const card = document.createElement("article");

            card.className = "project-card";

            const cover = document.createElement("div");
            cover.className = "project-card__cover";

            if (project.cover_url) {
                const image = document.createElement("img");

                image.src =
                    `${project.cover_url}?v=` +
                    encodeURIComponent(
                        project.updated_at || ""
                    );

                image.alt =
                    `Capa de ${project.titulo || "projeto"}`;

                cover.appendChild(image);
            } else {
                cover.textContent = "Sem capa";
            }

            const body = document.createElement("div");
            body.className = "project-card__body";

            const title = document.createElement("h3");
            title.textContent =
                project.titulo || "Projeto sem título";

            const subtitle = document.createElement("p");

            subtitle.textContent = [
                project.concurso,
                project.cargo,
            ]
                .filter(Boolean)
                .join(" • ") ||
                "Sem concurso/cargo informado";

            const meta = document.createElement("div");
            meta.className = "project-card__meta";

            const subjectMeta = document.createElement("span");
            subjectMeta.innerHTML =
                `<strong>${project.total_materias || 0}</strong> ` +
                "matéria(s)";

            const dateMeta = document.createElement("span");
            dateMeta.textContent =
                `Atualizado em ${formatProjectDate(project.updated_at)}`;

            meta.append(
                subjectMeta,
                dateMeta
            );

            body.append(
                title,
                subtitle,
                meta
            );

            const actions = document.createElement("div");
            actions.className = "project-card__actions";

            const openButton = document.createElement("button");

            openButton.type = "button";
            openButton.className =
                "project-action project-action--open";
            openButton.textContent = "Abrir";

            openButton.addEventListener(
                "click",
                () => openProject(
                    project.project_id
                )
            );

            const deleteButton = document.createElement("button");

            deleteButton.type = "button";
            deleteButton.className =
                "project-action project-action--delete";
            deleteButton.textContent = "Excluir";

            deleteButton.addEventListener(
                "click",
                () => deleteProject(
                    project.project_id,
                    project.titulo
                )
            );

            actions.append(
                openButton,
                deleteButton
            );

            card.append(
                cover,
                body,
                actions
            );

            projectsList.appendChild(
                card
            );
        });
    }

    async function openProjects() {
        projectsModal.hidden = false;
        document.body.style.overflow = "hidden";

        await loadProjects();
    }

    async function openProject(projectId) {
        try {
            const response = await fetch(
                `/api/projetos/${projectId}`,
                {
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    await responseError(response)
                );
            }

            const data = await response.json();
            const project = data.projeto;

            const dados = project.dados || {};
            const editorial = project.editorial || {};

            state.projectId =
                project.project_id;

            state.projectUpdatedAt =
                project.updated_at;

            Object.entries(dados).forEach(
                ([key, value]) => {
                    setFieldValue(
                        key,
                        value ?? ""
                    );
                }
            );

            Object.entries(editorial).forEach(
                ([key, value]) => {
                    setFieldValue(
                        key,
                        value
                    );
                }
            );

            state.selectedSubjects = (
                Array.isArray(project.materias)
                    ? project.materias
                    : []
            )
                .sort(
                    (a, b) =>
                        (a.ordem || 0) -
                        (b.ordem || 0)
                )
                .map((subject) => ({
                    id: subject.id_materia,
                    nome:
                        subject.materia ||
                        subject.id_materia,
                    codigo:
                        subject.codigo_materia ||
                        null,
                }));

            updateSubjectCards();
            renderSelectedSubjects();

            const coverMode =
                editorial.cover_mode ||
                "cover";

            coverPreview.classList.toggle(
                "contain",
                coverMode === "contain"
            );

            applyRemoteCover(project);

            updatePdfControls(
                project
            );

            saveDraft();
            markSaved();
            updateReview();

            closeProjects();

            goToStep(1);

            const integrity =
                project.integridade;

            if (
                integrity &&
                !integrity.ok
            ) {
                showToast(
                    "O projeto foi aberto, mas algumas matérias " +
                    "estão ausentes ou inválidas na biblioteca.",
                    "error"
                );
            } else {
                showToast(
                    "Projeto aberto com sucesso."
                );
            }

        } catch (error) {
            console.error(error);

            showToast(
                error.message ||
                "Não foi possível abrir o projeto.",
                "error"
            );
        }
    }

    async function deleteProject(projectId, title) {
        const confirmed = window.confirm(
            `Excluir o projeto "${title || "sem título"}"?\n\n` +
            "Esta ação remove também a capa e arquivos do projeto."
        );

        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch(
                `/api/projetos/${projectId}`,
                {
                    method: "DELETE",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    await responseError(response)
                );
            }

            if (state.projectId === projectId) {
                state.projectId = null;
                state.projectUpdatedAt = null;

                clearCoverPreview(false);

                markDirty(
                    "Projeto excluído — rascunho local"
                );

                saveDraft();
            }

            showToast(
                "Projeto excluído."
            );

            await loadProjects();

        } catch (error) {
            console.error(error);

            showToast(
                error.message ||
                "Não foi possível excluir o projeto.",
                "error"
            );
        }
    }

    function newProject() {
        const hasContent =
            getFieldValue("titulo").trim() ||
            getFieldValue("cargo").trim() ||
            state.selectedSubjects.length > 0;

        if (hasContent) {
            const confirmed = window.confirm(
                "Iniciar um novo projeto?\n\n" +
                "Alterações não salvas do projeto atual serão descartadas."
            );

            if (!confirmed) {
                return;
            }
        }

        releaseCoverUrl();

        state.projectId = null;
        state.projectUpdatedAt = null;
        state.coverFile = null;
        state.coverRemoved = false;
        state.selectedSubjects = [];

        form.reset();

        coverPreview.classList.remove(
            "contain"
        );

        clearCoverPreview(false);

        updateSubjectCards();
        renderSelectedSubjects();

        window.localStorage.removeItem(
            STORAGE_KEY
        );

        draftStatus.textContent =
            "Rascunho local";

        draftStatus.classList.remove(
            "is-saved",
            "is-dirty"
        );

        resetPdfControls();

        closeProjects();

        goToStep(1);

        updateReview();

        showToast(
            "Novo projeto iniciado."
        );
    }

    function resetPdfControls() {
        openPdfButton.hidden = true;
        downloadPdfButton.hidden = true;
        openAuditButton.hidden = true;

        openPdfButton.dataset.url = "";

        downloadPdfButton.href = "#";

        state.pdfAudit = null;

        pdfStatus.classList.remove(
            "is-ready",
            "is-stale",
            "is-error"
        );

        pdfStatus.innerHTML = `
            <strong>PDF ainda não gerado</strong>
            <span>
                O arquivo será composto em A4,
                validado e terá as páginas contabilizadas.
            </span>
        `;
    }

    function updatePdfControls(project) {
        const metadata =
            project &&
            typeof project.pdf_preview === "object"
                ? project.pdf_preview
                : null;

        if (!metadata || !state.projectId) {
            resetPdfControls();
            return;
        }

        const viewUrl =
            `/api/projetos/${state.projectId}/pdf/preview`;

        const downloadUrl =
            `/api/projetos/${state.projectId}/pdf/download`;

        openPdfButton.dataset.url =
            viewUrl;

        downloadPdfButton.href =
            downloadUrl;

        openPdfButton.hidden = false;
        downloadPdfButton.hidden = false;
        openAuditButton.hidden = false;

        pdfStatus.classList.remove(
            "is-ready",
            "is-stale",
            "is-error"
        );

        if (metadata.stale) {
            pdfStatus.classList.add(
                "is-stale"
            );

            pdfStatus.innerHTML = `
                <strong>PDF desatualizado</strong>
                <span>
                    O projeto mudou depois da última geração.
                    Gere novamente antes da entrega.
                </span>
            `;

            return;
        }

        pdfStatus.classList.add(
            "is-ready"
        );

        const pages =
            Number(
                metadata.paginas || 0
            );

        const size =
            formatBytes(
                Number(
                    metadata.tamanho_bytes || 0
                )
            );

        pdfStatus.innerHTML = `
            <strong>PDF validado</strong>
            <span>
                ${pages} página(s) • ${size}
            </span>
        `;
    }

    function auditStatusLabel(status) {
        if (status === "erro") {
            return "Erro";
        }

        if (status === "atencao") {
            return "Atenção";
        }

        return "OK";
    }

    function renderAuditSummary(audit) {
        const summary =
            audit &&
            typeof audit.resumo === "object"
                ? audit.resumo
                : {};

        const ok =
            Number(
                summary.paginas_ok || 0
            );

        const attention =
            Number(
                summary.paginas_atencao || 0
            );

        const errors =
            Number(
                summary.paginas_erro || 0
            );

        const total =
            Number(
                audit.total_paginas || 0
            );

        auditSummary.innerHTML = `
            <span class="audit-summary__item">
                <strong>${total}</strong>
                páginas
            </span>

            <span class="audit-summary__item audit-summary__item--ok">
                <strong>${ok}</strong>
                OK
            </span>

            <span class="audit-summary__item audit-summary__item--warning">
                <strong>${attention}</strong>
                atenção
            </span>

            <span class="audit-summary__item audit-summary__item--error">
                <strong>${errors}</strong>
                erro(s)
            </span>
        `;

        if (audit.stale) {
            const warning =
                document.createElement(
                    "div"
                );

            warning.className =
                "audit-stale-warning";

            warning.textContent =
                "Esta auditoria pertence a uma versão anterior do PDF.";

            auditSummary.prepend(
                warning
            );
        }

        const suspicious =
            Number(
                summary.paginas_suspeitas || 0
            );

        auditFooterStatus.textContent =
            suspicious === 0
                ? "Nenhuma página suspeita detectada."
                : `${suspicious} página(s) merecem revisão.`;
    }

    function createAuditIssue(issue) {
        const element =
            document.createElement(
                "div"
            );

        const severity =
            issue.gravidade ||
            "atencao";

        element.className =
            `audit-issue audit-issue--${severity}`;

        element.textContent =
            issue.mensagem ||
            issue.codigo ||
            "Verificação editorial.";

        return element;
    }

    function renderAuditPages(
        audit,
        filter = "all"
    ) {
        auditGrid.innerHTML = "";

        const pages =
            Array.isArray(
                audit.paginas
            )
                ? audit.paginas
                : [];

        const filtered =
            filter === "all"
                ? pages
                : pages.filter(
                    (page) =>
                        page.status === filter
                );

        if (filtered.length === 0) {
            auditGrid.innerHTML = `
                <div class="audit-empty">
                    Nenhuma página neste filtro.
                </div>
            `;

            return;
        }

        filtered.forEach((page) => {
            const card =
                document.createElement(
                    "article"
                );

            card.className =
                `audit-page audit-page--${page.status}`;

            card.dataset.status =
                page.status;

            const imageButton =
                document.createElement(
                    "button"
                );

            imageButton.type = "button";

            imageButton.className =
                "audit-page__image-button";

            imageButton.title =
                `Abrir PDF na página ${page.pagina}`;

            const image =
                document.createElement(
                    "img"
                );

            image.className =
                "audit-page__image";

            image.loading = "lazy";

            image.alt =
                `Miniatura da página ${page.pagina}`;

            image.src =
                `/api/projetos/${state.projectId}` +
                `/pdf/audit/pages/${page.pagina}`;

            imageButton.appendChild(
                image
            );

            imageButton.addEventListener(
                "click",
                () => {
                    window.open(
                        `/api/projetos/${state.projectId}` +
                        `/pdf/preview#page=${page.pagina}`,
                        "_blank",
                        "noopener"
                    );
                }
            );

            const body =
                document.createElement(
                    "div"
                );

            body.className =
                "audit-page__body";

            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "audit-page__header";

            const number =
                document.createElement(
                    "span"
                );

            number.className =
                "audit-page__number";

            number.textContent =
                `Página ${page.pagina}`;

            const badge =
                document.createElement(
                    "span"
                );

            badge.className =
                `audit-status-badge ` +
                `audit-status-badge--${page.status}`;

            badge.textContent =
                auditStatusLabel(
                    page.status
                );

            header.append(
                number,
                badge
            );

            const metrics =
                document.createElement(
                    "div"
                );

            metrics.className =
                "audit-page__metrics";

            const textMetric =
                document.createElement(
                    "div"
                );

            textMetric.className =
                "audit-page__metric";

            textMetric.innerHTML = `
                <span>Texto</span>
                <strong>
                    ${Number(page.caracteres_texto || 0).toLocaleString("pt-BR")}
                    caracteres
                </strong>
            `;

            const densityMetric =
                document.createElement(
                    "div"
                );

            densityMetric.className =
                "audit-page__metric";

            const density =
                Number(
                    page.densidade_tinta || 0
                ) * 100;

            densityMetric.innerHTML = `
                <span>Densidade visual</span>
                <strong>
                    ${density.toFixed(1)}%
                </strong>
            `;

            metrics.append(
                textMetric,
                densityMetric
            );

            const issues =
                document.createElement(
                    "div"
                );

            issues.className =
                "audit-page__issues";

            const pageIssues =
                Array.isArray(
                    page.problemas
                )
                    ? page.problemas
                    : [];

            if (
                pageIssues.length === 0
            ) {
                const okIssue =
                    document.createElement(
                        "div"
                    );

                okIssue.className =
                    "audit-issue";

                okIssue.textContent =
                    "Nenhuma anomalia automática detectada.";

                issues.appendChild(
                    okIssue
                );

            } else {
                pageIssues.forEach(
                    (issue) => {
                        issues.appendChild(
                            createAuditIssue(
                                issue
                            )
                        );
                    }
                );
            }

            body.append(
                header,
                metrics,
                issues
            );

            card.append(
                imageButton,
                body
            );

            auditGrid.appendChild(
                card
            );
        });
    }

    async function fetchAudit(
        method = "GET"
    ) {
        if (!state.projectId) {
            throw new Error(
                "Nenhum projeto está aberto."
            );
        }

        const response = await fetch(
            `/api/projetos/${state.projectId}/pdf/audit`,
            {
                method,
                headers: {
                    Accept: "application/json",
                },
            }
        );

        if (!response.ok) {
            throw new Error(
                await responseError(
                    response
                )
            );
        }

        const data =
            await response.json();

        return data.audit;
    }

    async function openAudit() {
        auditModal.hidden = false;

        document.body.style.overflow =
            "hidden";

        auditGrid.innerHTML = `
            <div class="audit-loading">
                Carregando miniaturas...
            </div>
        `;

        auditSummary.textContent =
            "Carregando auditoria...";

        try {
            let audit = null;

            try {
                audit = await fetchAudit(
                    "GET"
                );

            } catch (error) {
                audit = await fetchAudit(
                    "POST"
                );
            }

            state.pdfAudit =
                audit;

            renderAuditSummary(
                audit
            );

            renderAuditPages(
                audit,
                "all"
            );

            auditFilterButtons.forEach(
                (button) => {
                    button.classList.toggle(
                        "is-active",
                        button.dataset.auditFilter
                        === "all"
                    );
                }
            );

        } catch (error) {
            console.error(error);

            auditGrid.innerHTML = `
                <div class="audit-empty">
                    ${error.message ||
                    "Não foi possível carregar a auditoria."}
                </div>
            `;

            auditSummary.textContent =
                "Auditoria indisponível.";
        }
    }

    function closeAudit() {
        auditModal.hidden = true;

        document.body.style.overflow =
            "";
    }

    async function reauditPdf() {
        reauditPdfButton.disabled =
            true;

        const originalText =
            reauditPdfButton.textContent;

        reauditPdfButton.textContent =
            "Auditando...";

        try {
            const audit =
                await fetchAudit(
                    "POST"
                );

            state.pdfAudit =
                audit;

            renderAuditSummary(
                audit
            );

            renderAuditPages(
                audit,
                "all"
            );

            auditFilterButtons.forEach(
                (button) => {
                    button.classList.toggle(
                        "is-active",
                        button.dataset.auditFilter
                        === "all"
                    );
                }
            );

            showToast(
                "Auditoria visual concluída."
            );

        } catch (error) {
            console.error(error);

            showToast(
                error.message ||
                "Não foi possível auditar o PDF.",
                "error"
            );

        } finally {
            reauditPdfButton.disabled =
                false;

            reauditPdfButton.textContent =
                originalText;
        }
    }

    async function generatePreview() {
        generatePreviewButton.disabled = true;

        const originalContent =
            generatePreviewButton.innerHTML;

        generatePreviewButton.innerHTML =
            "Gerando PDF...";

        pdfStatus.classList.remove(
            "is-ready",
            "is-stale",
            "is-error"
        );

        pdfStatus.innerHTML = `
            <strong>Compondo apostila...</strong>
            <span>
                Aplicando paginação, sumário,
                cabeçalhos, caixas e validação.
            </span>
        `;

        try {
            const project =
                await saveProject();

            if (!project) {
                return;
            }

            const projectId =
                project.project_id;

            if (!projectId) {
                throw new Error(
                    "O projeto não possui identificador válido."
                );
            }

            const response = await fetch(
                `/api/projetos/${projectId}/pdf/preview`,
                {
                    method: "POST",
                    headers: {
                        Accept: "application/json",
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    await responseError(response)
                );
            }

            const data =
                await response.json();

            const metadata =
                data.pdf || {};

            const audit =
                data.audit || null;

            state.pdfAudit =
                audit;

            const pages =
                Number(
                    metadata.paginas || 0
                );

            const size =
                formatBytes(
                    Number(
                        metadata.tamanho_bytes || 0
                    )
                );

            openPdfButton.dataset.url =
                data.view_url;

            downloadPdfButton.href =
                data.download_url;

            openPdfButton.hidden = false;
            downloadPdfButton.hidden = false;
            openAuditButton.hidden = false;

            pdfStatus.classList.add(
                "is-ready"
            );

            const auditSummaryData =
                audit &&
                typeof audit.resumo === "object"
                    ? audit.resumo
                    : {};

            const suspiciousPages =
                Number(
                    auditSummaryData.paginas_suspeitas || 0
                );

            pdfStatus.innerHTML = `
                <strong>PDF gerado e validado</strong>
                <span>
                    ${pages} página(s) • ${size} •
                    ${suspiciousPages} página(s) para revisão automática
                </span>
            `;

            showToast(
                `PDF gerado com sucesso: ${pages} página(s).`
            );

            window.open(
                data.view_url,
                "_blank",
                "noopener"
            );

        } catch (error) {
            console.error(error);

            pdfStatus.classList.add(
                "is-error"
            );

            pdfStatus.innerHTML = `
                <strong>Falha na geração do PDF</strong>
                <span>
                    ${error.message || "Erro desconhecido."}
                </span>
            `;

            showToast(
                error.message ||
                "Não foi possível gerar o PDF.",
                "error"
            );

        } finally {
            generatePreviewButton.disabled = false;

            generatePreviewButton.innerHTML =
                originalContent;
        }
    }

    openPdfButton.addEventListener(
        "click",
        () => {
            const url =
                openPdfButton.dataset.url;

            if (!url) {
                return;
            }

            window.open(
                url,
                "_blank",
                "noopener"
            );
        }
    );

    openAuditButton.addEventListener(
        "click",
        openAudit
    );

    closeAuditModal.addEventListener(
        "click",
        closeAudit
    );

    auditModal.addEventListener(
        "click",
        (event) => {
            if (
                event.target
                === auditModal
            ) {
                closeAudit();
            }
        }
    );

    reauditPdfButton.addEventListener(
        "click",
        reauditPdf
    );

    auditOpenPdfButton.addEventListener(
        "click",
        () => {
            if (!state.projectId) {
                return;
            }

            window.open(
                `/api/projetos/${state.projectId}/pdf/preview`,
                "_blank",
                "noopener"
            );
        }
    );

    auditFilterButtons.forEach(
        (button) => {
            button.addEventListener(
                "click",
                () => {
                    auditFilterButtons.forEach(
                        (item) => {
                            item.classList.remove(
                                "is-active"
                            );
                        }
                    );

                    button.classList.add(
                        "is-active"
                    );

                    if (
                        !state.pdfAudit
                    ) {
                        return;
                    }

                    renderAuditPages(
                        state.pdfAudit,
                        button.dataset.auditFilter
                        || "all"
                    );
                }
            );
        }
    );

    saveProjectButton.addEventListener(
        "click",
        saveProject
    );

    generatePreviewButton.addEventListener(
        "click",
        generatePreview
    );

    openProjectsButton.addEventListener(
        "click",
        openProjects
    );

    newProjectButton.addEventListener(
        "click",
        newProject
    );

    closeProjectsModal.addEventListener(
        "click",
        closeProjects
    );

    refreshProjectsButton.addEventListener(
        "click",
        loadProjects
    );

    projectsNewButton.addEventListener(
        "click",
        newProject
    );

    projectsModal.addEventListener(
        "click",
        (event) => {
            if (event.target === projectsModal) {
                closeProjects();
            }
        }
    );

    async function loadPrompt() {
        if (state.promptText) {
            return state.promptText;
        }

        const response = await fetch(
            "/api/prompts/converter-materia",
            {
                headers: {
                    Accept: "text/plain",
                },
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        state.promptText = await response.text();

        return state.promptText;
    }

    function openPromptModal(text) {
        promptTextArea.value = text;

        promptSize.textContent =
            `${text.length.toLocaleString("pt-BR")} caracteres`;

        promptModal.hidden = false;

        document.body.style.overflow = "hidden";
    }

    function closePrompt() {
        promptModal.hidden = true;

        document.body.style.overflow = "";
    }

    async function copyPromptText(text) {
        if (
            navigator.clipboard &&
            typeof navigator.clipboard.writeText === "function"
        ) {
            await navigator.clipboard.writeText(text);
            return true;
        }

        return false;
    }

    async function handlePromptButton() {
        promptButton.disabled = true;

        try {
            const text = await loadPrompt();

            try {
                const copied = await copyPromptText(text);

                if (copied) {
                    showToast(
                        "Prompt JSON copiado para a área de transferência."
                    );

                    return;
                }
            } catch (clipboardError) {
                console.warn(
                    "Clipboard indisponível.",
                    clipboardError
                );
            }

            openPromptModal(text);

            showToast(
                "Não foi possível copiar automaticamente. " +
                "O prompt foi aberto para cópia manual.",
                "error"
            );
        } catch (error) {
            console.error(error);

            showToast(
                "Não foi possível carregar o Prompt JSON.",
                "error"
            );
        } finally {
            promptButton.disabled = false;
        }
    }

    promptButton.addEventListener("click", handlePromptButton);

    closePromptModal.addEventListener("click", closePrompt);

    promptModal.addEventListener("click", (event) => {
        if (event.target === promptModal) {
            closePrompt();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }

        if (!promptModal.hidden) {
            closePrompt();
            return;
        }

        if (!projectsModal.hidden) {
            closeProjects();
            return;
        }

        if (!auditModal.hidden) {
            closeAudit();
        }
    });

    modalCopyPrompt.addEventListener("click", async () => {
        try {
            await copyPromptText(promptTextArea.value);

            showToast(
                "Prompt copiado para a área de transferência."
            );
        } catch (error) {
            console.error(error);

            promptTextArea.focus();
            promptTextArea.select();

            showToast(
                "Use Ctrl+C para copiar o texto selecionado.",
                "error"
            );
        }
    });

    selectPromptButton.addEventListener("click", () => {
        promptTextArea.focus();
        promptTextArea.select();

        showToast(
            "Prompt selecionado. Pressione Ctrl+C para copiar."
        );
    });

    function formatBytes(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return "0 KB";
        }

        const kilobytes = bytes / 1024;

        if (kilobytes < 1024) {
            return `${kilobytes.toFixed(1)} KB`;
        }

        return `${(kilobytes / 1024).toFixed(2)} MB`;
    }

    function releaseCoverUrl() {
        if (
            state.coverUrl &&
            state.coverUrlIsObject
        ) {
            URL.revokeObjectURL(
                state.coverUrl
            );
        }

        state.coverUrl = null;
        state.coverUrlIsObject = false;
    }

    function clearCoverPreview(
        markAsRemoved = false
    ) {
        releaseCoverUrl();

        state.coverFile = null;

        if (markAsRemoved) {
            state.coverRemoved = true;
        }

        coverInput.value = "";

        coverPreviewImage.removeAttribute(
            "src"
        );

        coverPreviewImage.hidden = true;
        coverPreviewEmpty.hidden = false;
        coverFileInfo.hidden = true;
        removeCoverButton.hidden = true;

        updateReview();
    }

    function setCoverFile(file) {
        if (!file) {
            return;
        }

        const acceptedTypes = new Set([
            "image/png",
            "image/jpeg",
            "image/webp",
        ]);

        if (!acceptedTypes.has(file.type)) {
            showToast(
                "Formato de capa não suportado. Use PNG, JPG ou WEBP.",
                "error"
            );

            return;
        }

        releaseCoverUrl();

        state.coverFile = file;
        state.coverRemoved = false;

        state.coverUrl = URL.createObjectURL(file);
        state.coverUrlIsObject = true;

        coverPreviewImage.src = state.coverUrl;
        coverPreviewImage.hidden = false;
        coverPreviewEmpty.hidden = true;

        coverFileName.textContent = file.name;
        coverFileSize.textContent = formatBytes(file.size);

        coverFileInfo.hidden = false;
        removeCoverButton.hidden = false;

        markDirty();
        saveDraft();
        updateReview();
    }

    function removeCover() {
        clearCoverPreview(
            Boolean(state.projectId)
        );

        markDirty();
        saveDraft();
    }

    selectCoverButton.addEventListener("click", () => {
        coverInput.click();
    });

    coverInput.addEventListener("change", () => {
        const [file] = coverInput.files;

        setCoverFile(file);
    });

    removeCoverButton.addEventListener("click", removeCover);

    ["dragenter", "dragover"].forEach((eventName) => {
        coverDropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();

            coverDropzone.classList.add("is-dragging");
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        coverDropzone.addEventListener(eventName, (event) => {
            event.preventDefault();
            event.stopPropagation();

            coverDropzone.classList.remove("is-dragging");
        });
    });

    coverDropzone.addEventListener("drop", (event) => {
        const [file] = event.dataTransfer.files;

        setCoverFile(file);
    });

    form
        .querySelectorAll('input[name="cover_mode"]')
        .forEach((radio) => {
            radio.addEventListener("change", () => {
                coverPreview.classList.toggle(
                    "contain",
                    radio.value === "contain" && radio.checked
                );
            });
        });

    function getSubjectFromCard(card) {
        return {
            id: card.dataset.subjectId,
            nome: card.dataset.subjectName,
            codigo: card.dataset.subjectCode || null,
        };
    }

    function updateSubjectCards() {
        const selectedIds = new Set(
            state.selectedSubjects.map((item) => item.id)
        );

        subjectCards.forEach((card) => {
            const selected = selectedIds.has(
                card.dataset.subjectId
            );

            card.classList.toggle("is-selected", selected);

            const checkbox = card.querySelector(".subject-checkbox");

            if (checkbox && !checkbox.disabled) {
                checkbox.checked = selected;
            }
        });
    }

    function updateSelectedCounters() {
        const count = state.selectedSubjects.length;

        selectedCount.textContent = String(count);
        selectedCountHeading.textContent = String(count);
    }

    function moveSelectedSubject(id, direction) {
        const index = state.selectedSubjects.findIndex(
            (item) => item.id === id
        );

        if (index < 0) {
            return;
        }

        const targetIndex = index + direction;

        if (
            targetIndex < 0 ||
            targetIndex >= state.selectedSubjects.length
        ) {
            return;
        }

        const [item] = state.selectedSubjects.splice(index, 1);

        state.selectedSubjects.splice(targetIndex, 0, item);

        markDirty();
        renderSelectedSubjects();
        saveDraft();
    }

    function removeSelectedSubject(id) {
        state.selectedSubjects = state.selectedSubjects.filter(
            (item) => item.id !== id
        );

        markDirty();
        updateSubjectCards();
        renderSelectedSubjects();
        saveDraft();
    }

    function createMiniButton(label, pathData, extraClass = "") {
        const button = document.createElement("button");

        button.type = "button";
        button.className = `mini-action ${extraClass}`.trim();
        button.setAttribute("aria-label", label);
        button.title = label;

        button.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="${pathData}"></path>
            </svg>
        `;

        return button;
    }

    function renderSelectedSubjects() {
        selectedContainer
            .querySelectorAll(".selected-item")
            .forEach((item) => item.remove());

        selectedEmpty.hidden = state.selectedSubjects.length > 0;

        state.selectedSubjects.forEach((subject, index) => {
            const item = document.createElement("div");

            item.className = "selected-item";
            item.draggable = true;
            item.dataset.subjectId = subject.id;

            const handle = document.createElement("span");
            handle.className = "drag-handle";

            handle.innerHTML = `
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="8" cy="6" r="1.2"></circle>
                    <circle cx="16" cy="6" r="1.2"></circle>
                    <circle cx="8" cy="12" r="1.2"></circle>
                    <circle cx="16" cy="12" r="1.2"></circle>
                    <circle cx="8" cy="18" r="1.2"></circle>
                    <circle cx="16" cy="18" r="1.2"></circle>
                </svg>
            `;

            const order = document.createElement("span");
            order.className = "selected-item__order";
            order.textContent = String(index + 1);

            const name = document.createElement("span");
            name.className = "selected-item__name";
            name.textContent = subject.nome;
            name.title = subject.nome;

            const actions = document.createElement("div");
            actions.className = "selected-item__actions";

            const upButton = createMiniButton(
                "Mover para cima",
                "m18 15-6-6-6 6"
            );

            const downButton = createMiniButton(
                "Mover para baixo",
                "m6 9 6 6 6-6"
            );

            const removeButton = createMiniButton(
                "Remover matéria",
                "M6 6l12 12M18 6 6 18",
                "mini-action--danger"
            );

            upButton.disabled = index === 0;

            downButton.disabled =
                index === state.selectedSubjects.length - 1;

            upButton.addEventListener("click", () => {
                moveSelectedSubject(subject.id, -1);
            });

            downButton.addEventListener("click", () => {
                moveSelectedSubject(subject.id, 1);
            });

            removeButton.addEventListener("click", () => {
                removeSelectedSubject(subject.id);
            });

            actions.append(
                upButton,
                downButton,
                removeButton
            );

            item.append(
                handle,
                order,
                name,
                actions
            );

            item.addEventListener("dragstart", () => {
                draggedItem = item;

                item.classList.add("is-dragging");
            });

            item.addEventListener("dragend", () => {
                item.classList.remove("is-dragging");

                draggedItem = null;

                syncOrderFromDom();
            });

            selectedContainer.appendChild(item);
        });

        updateSelectedCounters();
        updateReview();
    }

    function getDragAfterElement(container, y) {
        const draggableElements = Array.from(
            container.querySelectorAll(
                ".selected-item:not(.is-dragging)"
            )
        );

        return draggableElements.reduce(
            (closest, child) => {
                const box = child.getBoundingClientRect();

                const offset =
                    y - box.top - box.height / 2;

                if (
                    offset < 0 &&
                    offset > closest.offset
                ) {
                    return {
                        offset,
                        element: child,
                    };
                }

                return closest;
            },
            {
                offset: Number.NEGATIVE_INFINITY,
                element: null,
            }
        ).element;
    }

    selectedContainer.addEventListener("dragover", (event) => {
        event.preventDefault();

        if (!draggedItem) {
            return;
        }

        const afterElement = getDragAfterElement(
            selectedContainer,
            event.clientY
        );

        if (!afterElement) {
            selectedContainer.appendChild(draggedItem);
        } else {
            selectedContainer.insertBefore(
                draggedItem,
                afterElement
            );
        }
    });

    function syncOrderFromDom() {
        const ids = Array.from(
            selectedContainer.querySelectorAll(".selected-item")
        ).map((item) => item.dataset.subjectId);

        const subjectMap = new Map(
            state.selectedSubjects.map(
                (subject) => [subject.id, subject]
            )
        );

        state.selectedSubjects = ids
            .map((id) => subjectMap.get(id))
            .filter(Boolean);

        markDirty();
        renderSelectedSubjects();
        saveDraft();
    }

    subjectCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const card = checkbox.closest(".subject-card");

            if (!card) {
                return;
            }

            const subject = getSubjectFromCard(card);

            if (checkbox.checked) {
                if (
                    !state.selectedSubjects.some(
                        (item) => item.id === subject.id
                    )
                ) {
                    state.selectedSubjects.push(subject);
                }
            } else {
                state.selectedSubjects =
                    state.selectedSubjects.filter(
                        (item) => item.id !== subject.id
                    );
            }

            markDirty();
            updateSubjectCards();
            renderSelectedSubjects();
            saveDraft();
        });
    });

    selectAllSubjects.addEventListener("click", () => {
        const currentIds = new Set(
            state.selectedSubjects.map((item) => item.id)
        );

        subjectCards.forEach((card) => {
            if (card.dataset.subjectValid !== "true") {
                return;
            }

            const subject = getSubjectFromCard(card);

            if (!subject.id || currentIds.has(subject.id)) {
                return;
            }

            state.selectedSubjects.push(subject);
            currentIds.add(subject.id);
        });

        markDirty();
        updateSubjectCards();
        renderSelectedSubjects();
        saveDraft();
    });

    clearSubjects.addEventListener("click", () => {
        state.selectedSubjects = [];

        markDirty();
        updateSubjectCards();
        renderSelectedSubjects();
        saveDraft();
    });

    subjectSearch.addEventListener("input", () => {
        const query = subjectSearch.value
            .trim()
            .toLocaleLowerCase("pt-BR");

        subjectCards.forEach((card) => {
            const haystack = [
                card.dataset.subjectName,
                card.dataset.subjectCode,
                card.textContent,
            ]
                .join(" ")
                .toLocaleLowerCase("pt-BR");

            card.classList.toggle(
                "subject-card--hidden",
                Boolean(query) && !haystack.includes(query)
            );
        });
    });

    function radioLabel(name, labels) {
        const value = getFieldValue(name);

        return labels[value] ?? "—";
    }

    function setChecklistState(selector, ok) {
        const element = document.querySelector(selector);

        if (!element) {
            return;
        }

        element.classList.toggle("is-ok", Boolean(ok));
    }

    function updateReview() {
        if (!reviewTitle) {
            return;
        }

        const title =
            getFieldValue("titulo").trim() ||
            "Apostila sem título";

        const contest =
            getFieldValue("concurso").trim();

        const position =
            getFieldValue("cargo").trim();

        const bank =
            getFieldValue("banca").trim();

        const year =
            getFieldValue("ano").trim();

        reviewTitle.textContent = title;

        reviewSubtitle.textContent =
            [contest, position]
                .filter(Boolean)
                .join(" • ") ||
            "Informe concurso e cargo.";

        reviewBank.textContent =
            bank || "Banca não informada";

        reviewYear.textContent =
            year || "Ano não informado";

        reviewCover.innerHTML = "";

        if (state.coverUrl) {
            const image = document.createElement("img");

            image.src = state.coverUrl;
            image.alt = "Capa selecionada";

            const mode = getFieldValue("cover_mode");

            image.style.objectFit =
                mode === "contain"
                    ? "contain"
                    : "cover";

            reviewCover.appendChild(image);
        } else {
            const span = document.createElement("span");

            span.textContent = "Sem capa";

            reviewCover.appendChild(span);
        }

        reviewSubjectList.innerHTML = "";

        if (state.selectedSubjects.length === 0) {
            const empty = document.createElement("li");

            empty.className = "review-empty";
            empty.textContent =
                "Nenhuma matéria selecionada.";

            reviewSubjectList.appendChild(empty);
        } else {
            state.selectedSubjects.forEach((subject) => {
                const item = document.createElement("li");

                item.textContent = subject.nome;

                reviewSubjectList.appendChild(item);
            });
        }

        const subjectCount = state.selectedSubjects.length;

        reviewSubjectCount.textContent =
            `${subjectCount} matéria${subjectCount === 1 ? "" : "s"}`;

        reviewExercises.textContent = radioLabel(
            "exercises_position",
            {
                after_subject: "Ao final de cada matéria",
                end_document: "Ao final da apostila",
            }
        );

        reviewAnswers.textContent = radioLabel(
            "answers_position",
            {
                after_subject: "Ao final de cada matéria",
                end_document: "Ao final da apostila",
            }
        );

        reviewReferences.textContent = radioLabel(
            "references_position",
            {
                after_subject: "Ao final de cada matéria",
                end_document: "Consolidadas ao final",
            }
        );

        reviewNewPage.textContent =
            getFieldValue("subject_new_page")
                ? "Iniciar cada matéria em nova página"
                : "Fluxo contínuo";

        setChecklistState(
            "#check-title",
            Boolean(getFieldValue("titulo").trim())
        );

        setChecklistState(
            "#check-cargo",
            Boolean(getFieldValue("cargo").trim())
        );

        setChecklistState(
            "#check-subjects",
            state.selectedSubjects.length > 0
        );

        const catalogCards = new Map(
            subjectCards.map(
                (card) => [
                    card.dataset.subjectId,
                    card,
                ]
            )
        );

        const selectedInvalid =
            state.selectedSubjects.some(
                (subject) => {
                    const card =
                        catalogCards.get(
                            subject.id
                        );

                    return (
                        !card ||
                        card.dataset.subjectValid !== "true"
                    );
                }
            );

        setChecklistState(
            "#check-library",
            !selectedInvalid
        );
    }

    restoreDraft();
    renderSelectedSubjects();
    goToStep(1);
});