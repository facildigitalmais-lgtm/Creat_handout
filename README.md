# Fácil Digital+ — Montador de Apostilas

Aplicação para criação, organização, composição, renderização e auditoria de apostilas didáticas da **Fácil Digital+**.

O projeto utiliza **Python + FastAPI** e trabalha com matérias estruturadas em **JSON**, permitindo reunir diferentes conteúdos em um projeto de apostila e posteriormente gerar um PDF padronizado.

## Objetivo do projeto

O `Creat_handout` foi desenvolvido para separar o **conteúdo pedagógico** da **diagramação final**.

Cada matéria pode ser armazenada em um arquivo JSON padronizado. A aplicação fica responsável por carregar a biblioteca, validar os arquivos, organizar o projeto, montar o conteúdo editorial, gerar o PDF e executar verificações de qualidade.

Entre os objetivos do sistema estão:

* manter uma biblioteca reutilizável de matérias;
* padronizar a estrutura das apostilas;
* combinar várias matérias em uma única apostila;
* validar os JSONs antes da utilização;
* gerar PDFs com identidade visual consistente;
* manter exercícios, gabaritos e referências estruturados;
* auditar o PDF gerado;
* facilitar a criação de diferentes apostilas sem precisar diagramar cada uma manualmente.

---

## Tecnologias principais

* Python
* FastAPI
* Uvicorn
* Jinja2
* JSON Schema
* WeasyPrint
* pypdf
* pypdfium2
* Pillow

As dependências Python do projeto estão declaradas em `requirements.txt`.

---

## Estrutura principal do projeto

```text
Creat_handout/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── renderers/
│   ├── services/
│   ├── validators/
│   ├── __init__.py
│   └── main.py
│
├── biblioteca/
│   └── _invalidos/
│
├── config/
├── logs/
├── output/
├── projetos/
├── prompts/
├── schemas/
├── scripts/
├── static/
├── temp/
├── templates/
├── uploads/
│   └── capas/
│
├── requirements.txt
└── README.md
```

## Executando no GitHub Codespaces

### 1. Abrir o Codespace

No repositório do GitHub, acesse:

**Code → Codespaces → Create codespace on main**

Ao abrir o terminal, o projeto normalmente estará em:

```bash
/workspaces/Creat_handout
```

Entre na pasta:

```bash
cd /workspaces/Creat_handout
```

Confira:

```bash
pwd
```

---

### 2. Criar o ambiente virtual

Este passo só é necessário se o `.venv` ainda não existir:

```bash
python -m venv .venv
```

---

### 3. Ativar o ambiente virtual

No Codespaces/Linux:

```bash
source .venv/bin/activate
```

Quando estiver ativo, o terminal deverá mostrar algo semelhante a:

```text
(.venv) @usuario ➜ /workspaces/Creat_handout (main) $
```

Para sair do ambiente:

```bash
deactivate
```

---

### 4. Atualizar o pip

Recomendado em um ambiente novo:

```bash
python -m pip install --upgrade pip
```

---

### 5. Instalar as dependências

Com o `.venv` ativo:

```bash
pip install -r requirements.txt
```

Para testar FastAPI e Uvicorn:

```bash
python -c "import fastapi, uvicorn; print('FastAPI:', fastapi.__version__); print('Uvicorn:', uvicorn.__version__)"
```

---

# Iniciar a aplicação

Com o ambiente ativo e na raiz do projeto:1

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O parâmetro `--reload` faz o servidor reiniciar automaticamente quando arquivos Python forem alterados durante o desenvolvimento.

---

## Abrir no Codespace

Depois que o Uvicorn iniciar, abra a aba:

**PORTS**

Localize:

```text
8000
```

Clique em:

**Open in Browser**

O GitHub Codespaces criará um endereço encaminhado para a aplicação.

---

# Comandos rápidos para iniciar no dia a dia

Se o `.venv` já estiver criado:

```bash
cd /workspaces/Creat_handout
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Essa é a sequência principal para continuar o desenvolvimento.

---

# Primeira configuração completa

Em um Codespace recém-criado:

```bash
cd /workspaces/Creat_handout
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Depois abra a porta `8000` pela aba **PORTS**.

---

# Documentação da API

Com a aplicação em execução, o FastAPI disponibiliza a documentação interativa.

## Swagger UI

```text
/docs
```

Em ambiente local:

```text
http://127.0.0.1:8000/docs
```

No Codespaces, acrescente `/docs` ao endereço da porta 8000.

## OpenAPI

```text
/openapi.json
```

---

# Testes rápidos do ambiente

## Verificar pypdfium2

```bash
python -c 'import importlib.metadata; print("pypdfium2:", importlib.metadata.version("pypdfium2"))'
```

## Verificar o serviço de auditoria

```bash
python -c 'from app.services.pdf_audit_service import pdf_audit_service; print("OK — PDFAuditService importado.")'
```

## Verificar as rotas

```bash
python -c 'from app.api.routes import router; print("OK — rotas:", len(router.routes))'
```

## Verificar a aplicação

```bash
python -c 'from app.main import app; print("OK — aplicação:", app.title)'
```

Se todos forem executados sem traceback, os principais módulos estão sendo carregados corretamente.

---

# Biblioteca de matérias

A aplicação utiliza matérias estruturadas em JSON.

A ideia é manter:

```text
1 arquivo JSON = 1 matéria completa
```

Exemplo:

```text
biblioteca/
├── lingua_portuguesa.json
├── matematica.json
├── historia.json
├── direito_administrativo.json
└── informatica.json
```

Antes de produzir toda a biblioteca, recomenda-se testar algumas matérias e conferir:

* validação do JSON;
* carregamento da biblioteca;
* organização dos capítulos;
* blocos didáticos;
* exercícios;
* gabaritos;
* referências;
* renderização;
* geração do PDF.

---

# Schema das matérias

Os arquivos da biblioteca devem seguir o JSON Schema adotado pelo projeto.

Os schemas estão em:

```text
schemas/
```

Isso permite que matérias de áreas completamente diferentes sejam processadas pelo mesmo pipeline editorial.

---

# Fluxo geral

```text
Matérias JSON
     ↓
Validação
     ↓
Biblioteca de matérias
     ↓
Criação do projeto
     ↓
Seleção das matérias
     ↓
Composição editorial
     ↓
Renderização
     ↓
Geração do PDF
     ↓
Auditoria do PDF
     ↓
Arquivo final
```

---

# Desenvolvimento

Sempre execute os comandos a partir da raiz:

```bash
cd /workspaces/Creat_handout
```

Confirme o Python ativo:

```bash
which python
```

O resultado deve apontar para algo semelhante a:

```text
/workspaces/Creat_handout/.venv/bin/python
```

Também é possível conferir:

```bash
which pip
which uvicorn
```

---

# Atualizar dependências

Quando `requirements.txt` for alterado:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Para listar as dependências instaladas:

```bash
pip list
```

---

# Atualizar o código

Verifique alterações:

```bash
git status
```

Atualize a branch:

```bash
git pull
```

Evite executar `git pull` sem revisar alterações locais ainda não commitadas.

---

# Salvar alterações no GitHub

Confira:

```bash
git status
```

Adicione:

```bash
git add .
```

Crie o commit:

```bash
git commit -m "Descrição da alteração"
```

Envie:

```bash
git push
```

---

# Encerrar o servidor

No terminal do Uvicorn:

```text
Ctrl + C
```

Depois, opcionalmente:

```bash
deactivate
```

---

# Solução de problemas

## `uvicorn: command not found`

Ative o ambiente:

```bash
source .venv/bin/activate
```

Instale novamente:

```bash
pip install -r requirements.txt
```

Ou execute:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## `ModuleNotFoundError: No module named 'app'`

Provavelmente o terminal não está na raiz do projeto.

Execute:

```bash
cd /workspaces/Creat_handout
```

Depois:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## O ambiente virtual não existe

Crie novamente:

```bash
cd /workspaces/Creat_handout
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Dependência não encontrada

Execute:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Se necessário:

```bash
python -m pip install --upgrade pip
```

---

## Porta 8000 já está em uso

Use temporariamente:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Depois abra a porta `8001` na aba **PORTS**.

---

## O servidor iniciou, mas a página não abre

Verifique:

1. se o Uvicorn continua rodando;
2. se não existe traceback no terminal;
3. se a porta correta aparece em **PORTS**;
4. se está abrindo o endereço encaminhado pelo Codespace;
5. se a aplicação está usando a porta correta.

---

# Comando recomendado

Para continuar o desenvolvimento normalmente:

```bash
cd /workspaces/Creat_handout
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Projeto

**Fácil Digital+ — Montador de Apostilas**

Sistema em desenvolvimento para automatizar a criação, organização, composição editorial, geração e auditoria de apostilas didáticas estruturadas.
