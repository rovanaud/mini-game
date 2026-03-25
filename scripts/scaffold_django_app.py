from __future__ import annotations

import argparse
import keyword
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
APPS_DIR = BACKEND_DIR / "apps"


BASE_FILES = {
    "__init__.py": "",
    "admin.py": "from django.contrib import admin\n",
    "models.py": "from django.db import models\n",
    "views.py": "",
    "urls.py": "",
    "services.py": '"""Application services for this domain."""\n',
    "selectors.py": '"""Read/query selectors for this domain."""\n',
}

OPTIONAL_FILES = {
    "policies": ("policies.py", '"""Authorization and business policy rules."""\n'),
    "runtime": ("runtime.py", '"""Runtime orchestration and execution logic."""\n'),
    "bracket": (
        "bracket.py",
        '"""Tournament bracket generation and progression logic."""\n',
    ),
    "visibility": ("visibility.py", '"""Visibility and scoping rules."""\n'),
    "registry": ("registry.py", '"""Plugin or component registry."""\n'),
    "spi": ("spi.py", '"""Service provider interface / extension contracts."""\n'),
    "rules": ("rules.py", '"""Domain rules and validation logic."""\n'),
    "serializers": ("serializers.py", '"""Serialization helpers."""\n'),
}


def to_class_name(app_name: str) -> str:
    return "".join(part.capitalize() for part in app_name.split("_"))


def validate_app_name(app_name: str) -> None:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", app_name):
        raise ValueError(
            "App name must be a valid Python module name in snake_case "
            "(example: identities, connect_four)."
        )
    if keyword.iskeyword(app_name):
        raise ValueError(f"'{app_name}' is a Python keyword and cannot be used.")


def write_file(path: Path, content: str, *, overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        print(f"skip  {path.relative_to(PROJECT_ROOT)}")
        return
    path.write_text(content, encoding="utf-8")
    print(f"write {path.relative_to(PROJECT_ROOT)}")


def build_apps_py(app_name: str) -> str:
    class_name = f"{to_class_name(app_name)}Config"
    return f'''from django.apps import AppConfig


class {class_name}(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.{app_name}"
    label = "{app_name}"
'''


def build_test_services_py(app_name: str) -> str:
    return f"""def test_{app_name}_scaffold_imports() -> None:
    assert True
"""


def ensure_package_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")
        print(f"write {init_file.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scaffold a Django app inside backend/apps/."
    )
    parser.add_argument("app_name", help="App name in snake_case, e.g. identities")
    parser.add_argument("--policies", action="store_true", help="Add policies.py")
    parser.add_argument("--runtime", action="store_true", help="Add runtime.py")
    parser.add_argument("--bracket", action="store_true", help="Add bracket.py")
    parser.add_argument("--visibility", action="store_true", help="Add visibility.py")
    parser.add_argument("--registry", action="store_true", help="Add registry.py")
    parser.add_argument("--spi", action="store_true", help="Add spi.py")
    parser.add_argument("--rules", action="store_true", help="Add rules.py")
    parser.add_argument("--serializers", action="store_true", help="Add serializers.py")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when applicable",
    )
    args = parser.parse_args()

    app_name = args.app_name.strip()
    validate_app_name(app_name)

    if not BACKEND_DIR.exists():
        raise SystemExit(
            f"backend/ not found at {BACKEND_DIR}. Run this script from your project."
        )

    ensure_package_dir(APPS_DIR)

    app_dir = APPS_DIR / app_name
    migrations_dir = app_dir / "migrations"
    tests_dir = app_dir / "tests"

    app_dir.mkdir(parents=True, exist_ok=True)
    migrations_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in BASE_FILES.items():
        write_file(app_dir / filename, content, overwrite=args.overwrite)

    write_file(app_dir / "apps.py", build_apps_py(app_name), overwrite=args.overwrite)
    write_file(migrations_dir / "__init__.py", "", overwrite=args.overwrite)
    write_file(tests_dir / "__init__.py", "", overwrite=args.overwrite)
    write_file(
        tests_dir / "test_services.py",
        build_test_services_py(app_name),
        overwrite=args.overwrite,
    )

    for option_name, (filename, content) in OPTIONAL_FILES.items():
        if getattr(args, option_name):
            write_file(app_dir / filename, content, overwrite=args.overwrite)

    print("\nDone.")
    print(f"App scaffolded in: {app_dir.relative_to(PROJECT_ROOT)}")

    class_name = f"{to_class_name(app_name)}Config"
    print("\nAdd this to INSTALLED_APPS:")
    print(f'    "apps.{app_name}.apps.{class_name}",')


if __name__ == "__main__":
    main()
