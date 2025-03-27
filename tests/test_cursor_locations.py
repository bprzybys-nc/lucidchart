#!/usr/bin/env python3
"""
Test module for cursor_locations.py.

This module contains unit tests for the Cursor data location detection functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import platform
import os
import pytest
from scripts.cursor_locations import (
    CursorPaths,
    get_cursor_paths,
    find_workspace_db,
    validate_paths,
    get_workspace_info
)

class TestCursorLocations(unittest.TestCase):
    """Test cases for cursor_locations module."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_home = Path("/test/home")
        self.test_workspace = Path("/test/workspace")
    
    def test_get_cursor_paths(self):
        """Test that get_cursor_paths returns a CursorPaths object."""
        with patch('pathlib.Path.home', return_value=self.test_home):
            paths = get_cursor_paths()
            self.assertIsInstance(paths, CursorPaths)
            self.assertIsInstance(paths.logs_dir, Path)
            self.assertIsInstance(paths.db_dir, Path)
            self.assertIsInstance(paths.workspace_storage, Path)
    
    def test_get_cursor_paths_macos(self):
        """Test path detection for macOS."""
        with patch('platform.system', return_value="Darwin"), \
             patch('pathlib.Path.home', return_value=self.test_home):
            paths = get_cursor_paths()
            expected_base = self.test_home / "Library" / "Application Support" / "Cursor"
            self.assertEqual(
                paths.logs_dir,
                expected_base / "logs"
            )
            self.assertEqual(
                paths.db_dir,
                expected_base / "User"
            )
            self.assertEqual(
                paths.workspace_storage,
                expected_base / "User" / "workspaceStorage"
            )
    
    def test_get_cursor_paths_linux(self):
        """Test path detection for Linux."""
        with patch('platform.system', return_value="Linux"), \
             patch('pathlib.Path.home', return_value=self.test_home):
            paths = get_cursor_paths()
            expected_base = self.test_home / ".config" / "Cursor"
            self.assertEqual(
                paths.logs_dir,
                expected_base / "logs"
            )
            self.assertEqual(
                paths.db_dir,
                expected_base / "User"
            )
            self.assertEqual(
                paths.workspace_storage,
                expected_base / "User" / "workspaceStorage"
            )
    
    def test_get_cursor_paths_windows(self):
        """Test path detection for Windows."""
        with patch('platform.system', return_value="Windows"), \
             patch.dict('os.environ', {'APPDATA': str(self.test_home)}), \
             patch('pathlib.Path.home', return_value=self.test_home):
            paths = get_cursor_paths()
            expected_base = Path(self.test_home) / "Cursor"
            self.assertEqual(
                paths.logs_dir,
                expected_base / "logs"
            )
            self.assertEqual(
                paths.db_dir,
                expected_base / "User"
            )
            self.assertEqual(
                paths.workspace_storage,
                expected_base / "User" / "workspaceStorage"
            )
    
    def test_find_workspace_db(self):
        """Test workspace database detection."""
        mock_workspace_path = "/test/workspace"
        mock_workspace_storage = MagicMock()
        mock_workspace_dir = MagicMock()
        mock_db_file = MagicMock()
        
        # Configure mocks
        mock_workspace_storage.exists.return_value = True
        mock_workspace_storage.iterdir.return_value = [mock_workspace_dir]
        
        mock_workspace_dir.is_dir.return_value = True
        
        # Make the mock dir / "state.vscdb" return our mock db file
        mock_workspace_dir.__truediv__.return_value = mock_db_file
        
        mock_db_file.exists.return_value = True
        
        # Set up the patch for get_cursor_paths
        with patch('scripts.cursor_locations.get_cursor_paths') as mock_get_paths:
            # Configure mock_get_paths to return our mock workspace storage
            mock_get_paths.return_value = CursorPaths(
                logs_dir=self.test_home / "logs",
                db_dir=self.test_home / "db",
                workspace_storage=mock_workspace_storage
            )
            
            # Run the function being tested
            result = find_workspace_db(mock_workspace_path)
            
            # Assert that the function returned the expected mock DB file
            self.assertEqual(result, mock_db_file)
            
            # Verify the mocks were called as expected
            mock_workspace_storage.exists.assert_called_once()
            mock_workspace_storage.iterdir.assert_called_once()
            mock_workspace_dir.is_dir.assert_called_once()
            mock_db_file.exists.assert_called_once()
    
    def test_validate_paths(self):
        """Test path validation."""
        # Create CursorPaths with proper structure
        paths = CursorPaths(
            logs_dir=self.test_home / "logs",
            db_dir=self.test_home / "db",
            workspace_storage=self.test_home / "workspaceStorage"
        )
        
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.is_dir') as mock_is_dir:
            # Setup exists and is_dir mocks
            mock_exists.return_value = True
            mock_is_dir.return_value = True
            
            validation = validate_paths(paths)
            
            self.assertEqual(validation, {
                "logs_dir": True,
                "db_dir": True,
                "workspace_storage": True
            })
    
    def test_get_workspace_info(self):
        """Test workspace information retrieval."""
        workspace_path = "/test/workspace"
        test_db_path = self.test_home / "db" / "state.vscdb"
        
        with patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'is_dir', return_value=True), \
             patch('scripts.cursor_locations.find_workspace_db', return_value=test_db_path):
            
            info = get_workspace_info(workspace_path)
            self.assertIsNotNone(info)
            self.assertEqual(info["path"], workspace_path)
            self.assertEqual(info["name"], "workspace")
            self.assertEqual(info["exists"], "True")
            self.assertEqual(info["is_dir"], "True")

if __name__ == '__main__':
    unittest.main() 