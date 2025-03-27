#!/usr/bin/env python3
"""
Cursor data location detection module.

This module provides functionality to detect and validate Cursor IDE's data storage locations
across different operating systems. It handles both database and log file locations.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, NamedTuple
import os
import platform
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OSType(Enum):
    """Supported operating system types."""
    MACOS = "Darwin"
    LINUX = "Linux"
    WINDOWS = "Windows"
    UNKNOWN = "Unknown"

class CursorPaths(NamedTuple):
    """Container for Cursor IDE's data storage paths."""
    logs_dir: Path
    db_dir: Path
    workspace_storage: Path

def get_os_type() -> OSType:
    """
    Detect the current operating system.
    
    Returns:
        OSType: Enum representing the current OS
    """
    system = platform.system()
    return OSType(system) if system in [e.value for e in OSType] else OSType.UNKNOWN

def get_home_dir() -> Path:
    """
    Get the user's home directory.
    
    Returns:
        Path: Path to user's home directory
    
    Raises:
        RuntimeError: If home directory cannot be determined
    """
    home = os.getenv('HOME') or os.getenv('USERPROFILE')
    if not home:
        raise RuntimeError("Could not determine user's home directory")
    return Path(home)

def get_cursor_paths() -> CursorPaths:
    """
    Get the default paths for Cursor IDE's data storage based on the operating system.
    
    Returns:
        CursorPaths: Named tuple containing paths for logs, database, and workspace storage
    """
    home = Path.home()
    system = platform.system()
    
    if system == "Darwin":  # macOS
        base_dir = home / "Library" / "Application Support" / "Cursor"
        logs_dir = base_dir / "logs"
        db_dir = base_dir / "User"
        workspace_storage = db_dir / "workspaceStorage"
    elif system == "Linux":
        base_dir = home / ".config" / "Cursor"
        logs_dir = base_dir / "logs"
        db_dir = base_dir / "User"
        workspace_storage = db_dir / "workspaceStorage"
    elif system == "Windows":
        base_dir = Path(os.getenv("APPDATA", "")) / "Cursor"
        logs_dir = base_dir / "logs"
        db_dir = base_dir / "User"
        workspace_storage = db_dir / "workspaceStorage"
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")
    
    return CursorPaths(logs_dir, db_dir, workspace_storage)

def find_workspace_db(workspace_path: str) -> Optional[Path]:
    """
    Find the database file for a specific workspace.
    
    Args:
        workspace_path: Path to the workspace directory
    
    Returns:
        Optional[Path]: Path to the workspace database if found, None otherwise
    """
    cursor_paths = get_cursor_paths()
    workspace_storage = cursor_paths.workspace_storage
    
    if not workspace_storage.exists():
        return None
    
    # Try to find a matching workspace directory
    for workspace_dir in workspace_storage.iterdir():
        if not workspace_dir.is_dir():
            continue
        
        # Look for state.vscdb file without extra checks
        db_file = workspace_dir / "state.vscdb"
        if db_file.exists():
            return db_file
    
    return None

def validate_paths(paths: CursorPaths) -> Dict[str, bool]:
    """
    Validate that the given paths exist and are accessible.
    
    Args:
        paths: CursorPaths tuple to validate
    
    Returns:
        Dict[str, bool]: Dictionary indicating which paths are valid
    """
    return {
        "logs_dir": paths.logs_dir.exists() and paths.logs_dir.is_dir(),
        "db_dir": paths.db_dir.exists() and paths.db_dir.is_dir(),
        "workspace_storage": paths.workspace_storage.exists() and paths.workspace_storage.is_dir()
    }

def get_workspace_info(workspace_path: str) -> Dict[str, str]:
    """
    Get information about a workspace.
    
    Args:
        workspace_path: Path to the workspace directory
    
    Returns:
        Dict[str, str]: Dictionary containing workspace information
    """
    workspace_path = Path(workspace_path)
    
    if not workspace_path.exists():
        return {"error": "Workspace path does not exist"}
    
    db_path = find_workspace_db(str(workspace_path))
    
    return {
        "path": str(workspace_path),
        "name": workspace_path.name,
        "db_path": str(db_path) if db_path else "Not found",
        "exists": str(workspace_path.exists()),
        "is_dir": str(workspace_path.is_dir())
    }

if __name__ == "__main__":
    # Example usage
    try:
        paths = get_cursor_paths()
        print(f"Workspace storage: {paths.workspace_storage}")
        print(f"Logs directory: {paths.logs_dir}")
        
        validation = validate_paths(paths)
        for path, valid in validation.items():
            print(f"{path}: {'✓' if valid else '✗'}")
            
    except Exception as e:
        logger.error(f"Error: {e}") 