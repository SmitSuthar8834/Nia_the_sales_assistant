#!/usr/bin/env python3
"""
Document Current Project Structure - Creates comprehensive documentation of the current state
"""
import json
from datetime import datetime
from pathlib import Path


def document_project_structure():
    """Document the current project structure before cleanup"""
    project_root = Path.cwd()

    structure_doc = {
        "documentation_date": datetime.now().isoformat(),
        "project_root": str(project_root),
        "total_files": 0,
        "total_directories": 0,
        "file_categories": {
            "documentation": [],
            "test_files": [],
            "python_modules": [],
            "static_files": [],
            "templates": [],
            "configuration": [],
            "temporary_debug": [],
            "other": [],
        },
        "directory_structure": {},
        "root_directory_files": [],
        "django_apps": [],
    }

    # Categorize files
    for file_path in project_root.rglob("*"):
        if file_path.is_file():
            structure_doc["total_files"] += 1
            relative_path = str(file_path.relative_to(project_root))

            # Categorize files
            if file_path.suffix == ".md":
                structure_doc["file_categories"]["documentation"].append(relative_path)
            elif file_path.name.startswith("test_") and file_path.suffix == ".py":
                structure_doc["file_categories"]["test_files"].append(relative_path)
            elif file_path.suffix == ".py":
                structure_doc["file_categories"]["python_modules"].append(relative_path)
            elif "static" in str(file_path):
                structure_doc["file_categories"]["static_files"].append(relative_path)
            elif "template" in str(file_path):
                structure_doc["file_categories"]["templates"].append(relative_path)
            elif file_path.name in [
                ".env",
                ".env.example",
                "requirements.txt",
                "docker-compose.yml",
            ]:
                structure_doc["file_categories"]["configuration"].append(relative_path)
            elif any(
                prefix in file_path.name
                for prefix in ["debug_", "quick_", "simple_", "restart_"]
            ):
                structure_doc["file_categories"]["temporary_debug"].append(
                    relative_path
                )
            else:
                structure_doc["file_categories"]["other"].append(relative_path)

        elif file_path.is_dir():
            structure_doc["total_directories"] += 1

    # Document root directory files
    for item in project_root.iterdir():
        if item.is_file():
            structure_doc["root_directory_files"].append(item.name)

    # Identify Django apps
    for item in project_root.iterdir():
        if item.is_dir() and (item / "apps.py").exists():
            structure_doc["django_apps"].append(item.name)

    # Create directory tree
    def build_tree(path, max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return "..."

        tree = {}
        try:
            for item in path.iterdir():
                if item.name.startswith(".") and item.name not in [
                    ".env",
                    ".env.example",
                ]:
                    continue
                if item.is_dir():
                    tree[f"{item.name}/"] = build_tree(
                        item, max_depth, current_depth + 1
                    )
                else:
                    tree[item.name] = f"file ({item.stat().st_size} bytes)"
        except PermissionError:
            tree["<permission denied>"] = ""
        return tree

    structure_doc["directory_structure"] = build_tree(project_root)

    # Save documentation
    with open("cleanup_scripts/current_project_structure.json", "w") as f:
        json.dump(structure_doc, f, indent=2)

    # Create human-readable summary
    summary = f"""# Current Project Structure Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- Total Files: {structure_doc['total_files']}
- Total Directories: {structure_doc['total_directories']}
- Root Directory Files: {len(structure_doc['root_directory_files'])}
- Django Applications: {len(structure_doc['django_apps'])}

## Root Directory Files ({len(structure_doc['root_directory_files'])} files)
{chr(10).join(f"- {f}" for f in sorted(structure_doc['root_directory_files']))}

## File Categories

### Documentation Files ({len(structure_doc['file_categories']['documentation'])} files)
{chr(10).join(f"- {f}" for f in sorted(structure_doc['file_categories']['documentation']))}

### Test Files ({len(structure_doc['file_categories']['test_files'])} files)
{chr(10).join(f"- {f}" for f in sorted(structure_doc['file_categories']['test_files']))}

### Temporary/Debug Files ({len(structure_doc['file_categories']['temporary_debug'])} files)
{chr(10).join(f"- {f}" for f in sorted(structure_doc['file_categories']['temporary_debug']))}

### Django Applications
{chr(10).join(f"- {app}/" for app in sorted(structure_doc['django_apps']))}

## Cleanup Recommendations

### Files to Move
1. **Documentation files** -> docs/ directory
   - {len(structure_doc['file_categories']['documentation'])} markdown files need organization

2. **Test files** -> tests/ directory  
   - {len(structure_doc['file_categories']['test_files'])} test files need organization

3. **Debug/Utility scripts** -> scripts/ directory
   - {len(structure_doc['file_categories']['temporary_debug'])} temporary files need cleanup

### Directories to Create
- docs/ (with subdirectories: api/, implementation/, setup/)
- tests/ (with subdirectories for each Django app)
- scripts/ (for utility scripts)
- config/ (for configuration files)

### Files Recommended for Removal
{chr(10).join(f"- {f} (temporary/debug file)" for f in structure_doc['file_categories']['temporary_debug'] if any(x in f for x in ['debug_', 'quick_', 'simple_']))}

## Next Steps
1. Create backup (✓ completed)
2. Create new directory structure
3. Move files systematically by category
4. Update imports and references
5. Validate functionality after each phase
"""

    with open(
        "cleanup_scripts/current_structure_summary.md", "w", encoding="utf-8"
    ) as f:
        f.write(summary)

    print("Project structure documentation completed!")
    print(f"- Detailed JSON: cleanup_scripts/current_project_structure.json")
    print(f"- Human-readable summary: cleanup_scripts/current_structure_summary.md")
    print(f"- Total files documented: {structure_doc['total_files']}")
    print(f"- Root directory files: {len(structure_doc['root_directory_files'])}")

    return structure_doc


if __name__ == "__main__":
    document_project_structure()
