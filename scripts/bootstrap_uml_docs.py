from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

UML_FILES = {
    "docs/uml/domain": [
        "01-core-domain-class.puml",
        "07-tournament-class.puml",
    ],
    "docs/uml/states": [
        "02-room-state.puml",
        "03-participant-state.puml",
        "04-match-state.puml",
        "08-tournament-state.puml",
        "21-proposal-state.puml",
        "22-chat-message-state.puml",
    ],
    "docs/uml/sequences": [
        "05-room-create-join-reconnect-sequence.puml",
        "06-connect-four-match-sequence.puml",
        "13-reconnect-recovery-sequence.puml",
        "14-host-transfer-sequence.puml",
        "15-tournament-progression-sequence.puml",
        "20-proposal-vote-sequence.puml",
        "23-admin-moderation-sequence.puml",
        "24-stats-event-ingestion.puml",
    ],
    "docs/uml/architecture": [
        "10-game-plugin-component.puml",
        "12-backend-component.puml",
        "16-deployment-runtime.puml",
        "17-package-module-dependencies.puml",
        "18-authoritative-game-state-ownership.puml",
    ],
    "docs/uml/data": [
        "19-er-data-model.puml",
    ],
    "docs/uml/moderation": [
        "09-authorization-activity.puml",
        "11-chat-visibility-scope.puml",
    ],
}

README_CONTENT = """# UML Documentation

This folder contains PlantUML source files for the system design of the project.

## Structure

- `domain/` → Core domain and business model diagrams
- `states/` → State machine diagrams
- `sequences/` → Interaction and workflow sequence diagrams
- `architecture/` → System, backend, deployment, and module architecture
- `data/` → Entity-relationship and data model diagrams
- `moderation/` → Authorization, chat visibility, and moderation diagrams

## Notes

- All files are written in PlantUML (`.puml`)
- Generated diagram images (PNG/SVG) should **not** be committed unless needed
- Keep file numbering stable to preserve references in documentation

"""

PLANTUML_TEMPLATE = """@startuml
title {title}

' TODO: Add diagram content

@enduml
"""


def humanize_title(filename: str) -> str:
    name = filename.removesuffix(".puml")
    parts = name.split("-", maxsplit=1)
    if len(parts) == 2 and parts[0].isdigit():
        name = parts[1]
    return name.replace("-", " ").title()


def create_file(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")
        print(f"Created: {path}")
    else:
        print(f"Skipped (already exists): {path}")


def main() -> None:
    for folder, files in UML_FILES.items():
        dir_path = PROJECT_ROOT / folder
        dir_path.mkdir(parents=True, exist_ok=True)

        for filename in files:
            file_path = dir_path / filename
            title = humanize_title(filename)
            create_file(file_path, PLANTUML_TEMPLATE.format(title=title))

    readme_path = PROJECT_ROOT / "docs" / "uml" / "README.md"
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    create_file(readme_path, README_CONTENT)

    print("\nUML documentation scaffold created successfully.")


if __name__ == "__main__":
    main()
