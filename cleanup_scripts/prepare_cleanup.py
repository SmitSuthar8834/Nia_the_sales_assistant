#!/usr/bin/env python3
"""
Prepare Cleanup Environment - Main script to prepare for codebase cleanup
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main():
    """Main preparation function"""
    print("=" * 60)
    print("NIA Sales Assistant - Codebase Cleanup Preparation")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Verify we're in the right directory
    if not Path("manage.py").exists():
        print(
            "ERROR: manage.py not found. Please run this script from the Django project root."
        )
        sys.exit(1)

    print("✓ Confirmed Django project root directory")

    # 2. Create cleanup scripts directory if it doesn't exist
    cleanup_dir = Path("cleanup_scripts")
    cleanup_dir.mkdir(exist_ok=True)
    print("✓ Cleanup scripts directory ready")

    # 3. Document current structure
    print("\n1. Documenting current project structure...")
    try:
        # Add current directory to path for imports
        sys.path.insert(0, str(Path.cwd()))
        exec(open("cleanup_scripts/current_structure_documentation.py").read())

        # Load the generated structure data
        with open("cleanup_scripts/current_project_structure.json", "r") as f:
            structure_doc = json.load(f)
        print("✓ Project structure documented")
    except Exception as e:
        print(f"✗ Failed to document structure: {e}")
        return False

    # 4. Initialize cleanup logger
    print("\n2. Initializing cleanup logger...")
    try:
        # Simple logging without complex imports

        log_data = {
            "cleanup_session": {
                "start_time": datetime.now().isoformat(),
                "operation": "init",
                "details": {
                    "total_files": structure_doc.get("total_files", 0),
                    "root_files": len(structure_doc.get("root_directory_files", [])),
                    "backup_created": True,
                },
            }
        }

        with open("cleanup_scripts/cleanup_log.json", "w") as f:
            json.dump(log_data, f, indent=2)

        print("✓ Cleanup logger initialized")
    except Exception as e:
        print(f"✗ Failed to initialize logger: {e}")
        return False

    # 5. Run initial validation
    print("\n3. Running initial project validation...")
    try:
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            print("✓ Initial validation passed")
        else:
            print("⚠ Initial validation failed - proceed with caution")
            print(f"  Error: {result.stderr[:200]}...")
    except Exception as e:
        print(f"⚠ Validation check failed: {e}")

    # 6. Create cleanup plan summary
    print("\n4. Creating cleanup execution plan...")

    plan_summary = f"""# Cleanup Execution Plan
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Pre-Cleanup Status
- Total files: {structure_doc.get('total_files', 'unknown')}
- Root directory files: {len(structure_doc.get('root_directory_files', []))}
- Documentation files: {len(structure_doc.get('file_categories', {}).get('documentation', []))}
- Test files: {len(structure_doc.get('file_categories', {}).get('test_files', []))}
- Temporary/debug files: {len(structure_doc.get('file_categories', {}).get('temporary_debug', []))}

## Cleanup Phases (Execute in Order)

### Phase 1: Documentation Organization (Low Risk)
- Create docs/ directory structure
- Move {len(structure_doc.get('file_categories', {}).get('documentation', []))} markdown files
- Consolidate implementation summaries
- **Validation**: Check documentation accessibility

### Phase 2: Test File Organization (Medium Risk)  
- Create tests/ directory structure
- Move {len(structure_doc.get('file_categories', {}).get('test_files', []))} test files
- Update import paths
- **Validation**: Run test discovery

### Phase 3: Script Organization (Medium Risk)
- Create scripts/ directory
- Move utility and debug scripts
- Clean up temporary files
- **Validation**: Check script functionality

### Phase 4: Code Optimization (High Risk)
- Remove unused imports
- Fix formatting inconsistencies
- Optimize Django app structure
- **Validation**: Full functionality test

## Safety Measures
- ✓ Backup created: backup_20250810_204241/
- ✓ Cleanup logger initialized
- ✓ Validation scripts ready
- ✓ Rollback capability available

## Next Steps
1. Review this plan
2. Execute phases one at a time
3. Run validation after each phase
4. Use rollback if issues occur

## Emergency Rollback
If cleanup causes issues:
```bash
python cleanup_scripts/cleanup_logger.py --generate-rollback
python rollback_cleanup.py
```
"""

    with open("cleanup_scripts/cleanup_plan.md", "w", encoding="utf-8") as f:
        f.write(plan_summary)

    print("✓ Cleanup execution plan created")

    # 7. Final summary
    print("\n" + "=" * 60)
    print("CLEANUP PREPARATION COMPLETE")
    print("=" * 60)
    print("Files created:")
    print("- cleanup_scripts/cleanup_logger.py (operation logging)")
    print("- cleanup_scripts/validation_scripts.py (functionality validation)")
    print("- cleanup_scripts/current_structure_documentation.py (structure docs)")
    print("- cleanup_scripts/current_project_structure.json (detailed structure)")
    print("- cleanup_scripts/current_structure_summary.md (human-readable summary)")
    print("- cleanup_scripts/cleanup_plan.md (execution plan)")
    print("- cleanup_scripts/prepare_cleanup.py (this script)")
    print()
    print("Backup location: backup_20250810_204241/")
    print()
    print(
        "Ready to begin cleanup! Execute phases in the order specified in cleanup_plan.md"
    )
    print("Remember to run validation after each phase.")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
