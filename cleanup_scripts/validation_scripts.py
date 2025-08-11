#!/usr/bin/env python3
"""
Validation Scripts - Verify project functionality after cleanup operations
"""
import importlib.util
import subprocess
import sys
from pathlib import Path


class ProjectValidator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.validation_results = []

    def validate_django_startup(self):
        """Test that Django can start without errors"""
        print("Validating Django startup...")
        try:
            result = subprocess.run(
                [sys.executable, "manage.py", "check", "--deploy"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.validation_results.append(
                    ("Django Startup", "PASS", "Django check passed")
                )
                return True
            else:
                self.validation_results.append(
                    ("Django Startup", "FAIL", result.stderr)
                )
                return False
        except subprocess.TimeoutExpired:
            self.validation_results.append(
                ("Django Startup", "FAIL", "Timeout during Django check")
            )
            return False
        except Exception as e:
            self.validation_results.append(("Django Startup", "FAIL", str(e)))
            return False

    def validate_imports(self, file_paths=None):
        """Validate that Python files can be imported without errors"""
        print("Validating Python imports...")

        if file_paths is None:
            # Find all Python files
            file_paths = list(self.project_root.rglob("*.py"))
            # Exclude certain directories
            file_paths = [
                f
                for f in file_paths
                if not any(
                    part in str(f)
                    for part in [
                        "__pycache__",
                        "migrations",
                        "backup_",
                        "cleanup_scripts",
                    ]
                )
            ]

        failed_imports = []

        for file_path in file_paths:
            try:
                spec = importlib.util.spec_from_file_location("test_module", file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception as e:
                failed_imports.append((str(file_path), str(e)))

        if failed_imports:
            self.validation_results.append(
                ("Import Validation", "FAIL", f"Failed imports: {len(failed_imports)}")
            )
            for file_path, error in failed_imports[:5]:  # Show first 5 errors
                print(f"  Import error in {file_path}: {error}")
            return False
        else:
            self.validation_results.append(
                (
                    "Import Validation",
                    "PASS",
                    f"All {len(file_paths)} files imported successfully",
                )
            )
            return True

    def validate_test_discovery(self):
        """Validate that tests can be discovered"""
        print("Validating test discovery...")
        try:
            result = subprocess.run(
                [sys.executable, "manage.py", "test", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.validation_results.append(
                    ("Test Discovery", "PASS", "Tests discovered successfully")
                )
                return True
            else:
                self.validation_results.append(
                    ("Test Discovery", "FAIL", result.stderr)
                )
                return False
        except Exception as e:
            self.validation_results.append(("Test Discovery", "FAIL", str(e)))
            return False

    def validate_static_files(self):
        """Validate static files collection"""
        print("Validating static files...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "manage.py",
                    "collectstatic",
                    "--dry-run",
                    "--noinput",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.validation_results.append(
                    ("Static Files", "PASS", "Static files validation passed")
                )
                return True
            else:
                self.validation_results.append(("Static Files", "FAIL", result.stderr))
                return False
        except Exception as e:
            self.validation_results.append(("Static Files", "FAIL", str(e)))
            return False

    def validate_directory_structure(self, expected_structure):
        """Validate that expected directories exist"""
        print("Validating directory structure...")
        missing_dirs = []

        for dir_path in expected_structure:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)

        if missing_dirs:
            self.validation_results.append(
                ("Directory Structure", "FAIL", f"Missing directories: {missing_dirs}")
            )
            return False
        else:
            self.validation_results.append(
                ("Directory Structure", "PASS", "All expected directories exist")
            )
            return True

    def run_full_validation(self):
        """Run all validation checks"""
        print("Starting full project validation...")

        # Expected directory structure after cleanup
        expected_dirs = [
            "docs",
            "docs/api",
            "docs/implementation",
            "docs/setup",
            "tests",
            "tests/ai_service",
            "tests/meeting_service",
            "tests/voice_service",
            "tests/users",
            "tests/utils",
            "scripts",
            "config",
        ]

        validations = [
            self.validate_directory_structure(expected_dirs),
            self.validate_django_startup(),
            self.validate_imports(),
            self.validate_test_discovery(),
            self.validate_static_files(),
        ]

        # Print results
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)

        for test_name, status, details in self.validation_results:
            status_symbol = "✓" if status == "PASS" else "✗"
            print(f"{status_symbol} {test_name}: {status}")
            if status == "FAIL":
                print(f"  Details: {details}")

        passed = sum(1 for _, status, _ in self.validation_results if status == "PASS")
        total = len(self.validation_results)

        print(f"\nValidation Summary: {passed}/{total} tests passed")

        return all(validations)


def run_quick_validation():
    """Quick validation for immediate feedback"""
    validator = ProjectValidator()
    return validator.validate_django_startup()


if __name__ == "__main__":
    validator = ProjectValidator()
    success = validator.run_full_validation()
    sys.exit(0 if success else 1)
