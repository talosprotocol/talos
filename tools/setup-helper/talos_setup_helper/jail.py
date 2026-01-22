import os
import shutil
from pathlib import Path
from typing import Optional

class JailError(Exception):
    """Security violation attempting to escape workspace jail"""
    pass

class WorkspaceJail:
    """
    Enforces strict filesystem isolation for job execution.
    All operations must be contained within root_path.
    Explicitly rejects symlinks to prevent escapes.
    """
    def __init__(self, root_path: Path):
        self.root = root_path.resolve()
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)
            
    def _validate_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path against the jail root and verify:
        1. It is not absolute
        2. It resolves to a path inside root
        3. No component of the path is a symlink (Strict Mode)
        """
        if os.path.isabs(relative_path):
            raise JailError(f"Absolute paths not allowed: {relative_path}")
            
        # Prevent initial traversal attempts
        if ".." in relative_path.split(os.sep):
             raise JailError(f"Path traversal detected in input: {relative_path}")

        full_path = (self.root / relative_path).resolve()
        
        # 1. Jail Break Check
        try:
            full_path.relative_to(self.root)
        except ValueError:
            raise JailError(f"Path escapes workspace root: {relative_path}")
            
        # 2. Symlink Check (Walk the path to ensure no components are links)
        # Note: We check existing components. For new files, we ensure we aren't writing THROUGH a link.
        current = full_path
        while current != self.root.parent:
            if current.exists() and current.is_symlink():
                raise JailError(f"Symlink detected in path: {current}")
            if current == self.root:
                break
            current = current.parent
            
        return full_path

    def create_job_dir(self, job_id: str) -> Path:
        """Create a dedicated directory for a job, ensuring it's clean"""
        safe_id = "".join(c for c in job_id if c.isalnum() or c in "-_)")
        job_dir = self._validate_path(safe_id)
        
        if job_dir.exists():
            # In a real implementation we might want to fail or archive
            # For now, we strictly ensure we aren't following links during deletion
            if job_dir.is_symlink():
                raise JailError(f"Existing job dir is a symlink: {safe_id}")
            shutil.rmtree(job_dir)
            
        job_dir.mkdir()
        return job_dir
