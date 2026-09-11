from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIR = PROJECT_ROOT / "app"
CONFIG_DIR = PROJECT_ROOT / "config"
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

LIBRARY_DIR = PROJECT_ROOT / "biblioteca"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
STATIC_DIR = PROJECT_ROOT / "static"

PROJECTS_DIR = PROJECT_ROOT / "projetos"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"

SETTINGS_FILE = CONFIG_DIR / "settings.json"

DEFAULT_SCHEMA_FILE = SCHEMAS_DIR / "apostila-subject.schema.json"
DEFAULT_PROMPT_TEMPLATE_FILE = (
    PROMPTS_DIR / "converter-apostila-para-json.txt"
)


def ensure_runtime_directories() -> None:
    directories = (
        PROMPTS_DIR,
        LIBRARY_DIR,
        LIBRARY_DIR / "_invalidos",
        PROJECTS_DIR,
        UPLOADS_DIR,
        UPLOADS_DIR / "capas",
        TEMP_DIR,
        TEMP_DIR / "html",
        TEMP_DIR / "pdf",
        OUTPUT_DIR,
        LOGS_DIR,
    )

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)