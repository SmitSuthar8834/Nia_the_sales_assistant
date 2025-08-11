#!/usr/bin/env python3
"""
Cleanup Logger - Tracks all cleanup operations for rollback capability
"""
import datetime
import json
import os


class CleanupLogger:
    def __init__(self, log_file="cleanup_log.json"):
        self.log_file = log_file
        self.operations = []
        self.start_time = datetime.datetime.now()

    def log_operation(
        self, operation_type, source_path, destination_path=None, details=None
    ):
        """Log a cleanup operation"""
        operation = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation_type": operation_type,  # move, delete, create, modify
            "source_path": str(source_path),
            "destination_path": str(destination_path) if destination_path else None,
            "details": details or {},
        }
        self.operations.append(operation)
        self._save_log()

    def log_file_move(self, source, destination):
        """Log a file move operation"""
        self.log_operation(
            "move",
            source,
            destination,
            {"file_size": os.path.getsize(source) if os.path.exists(source) else 0},
        )

    def log_file_delete(self, file_path, reason="cleanup"):
        """Log a file deletion"""
        self.log_operation(
            "delete",
            file_path,
            details={
                "reason": reason,
                "file_size": (
                    os.path.getsize(file_path) if os.path.exists(file_path) else 0
                ),
            },
        )

    def log_directory_create(self, dir_path):
        """Log directory creation"""
        self.log_operation("create_dir", dir_path)

    def log_code_modification(self, file_path, modification_type, details):
        """Log code modifications like import removal"""
        self.log_operation(
            "modify",
            file_path,
            details={"modification_type": modification_type, **details},
        )

    def _save_log(self):
        """Save the log to file"""
        log_data = {
            "cleanup_session": {
                "start_time": self.start_time.isoformat(),
                "last_update": datetime.datetime.now().isoformat(),
                "total_operations": len(self.operations),
            },
            "operations": self.operations,
        }

        with open(self.log_file, "w") as f:
            json.dump(log_data, f, indent=2)

    def generate_rollback_script(self, output_file="rollback_cleanup.py"):
        """Generate a rollback script based on logged operations"""
        rollback_commands = []

        for op in reversed(self.operations):
            if op["operation_type"] == "move":
                # Reverse the move
                rollback_commands.append(
                    f"shutil.move('{op['destination_path']}', '{op['source_path']}')"
                )
            elif op["operation_type"] == "delete":
                # Cannot restore deleted files, but log the issue
                rollback_commands.append(
                    f"# WARNING: Cannot restore deleted file: {op['source_path']}"
                )
            elif op["operation_type"] == "create_dir":
                # Remove created directory if empty
                rollback_commands.append(
                    f"try:\n    os.rmdir('{op['source_path']}')\nexcept OSError:\n    pass  # Directory not empty"
                )

        rollback_script = f"""#!/usr/bin/env python3
'''
Rollback script generated from cleanup operations
Generated at: {datetime.datetime.now().isoformat()}
'''
import os
import shutil

def rollback_cleanup():
    print("Starting cleanup rollback...")
    
{chr(10).join('    ' + cmd for cmd in rollback_commands)}
    
    print("Rollback completed!")

if __name__ == "__main__":
    rollback_cleanup()
"""

        with open(output_file, "w") as f:
            f.write(rollback_script)

        print(f"Rollback script generated: {output_file}")


# Global logger instance
cleanup_logger = CleanupLogger()
