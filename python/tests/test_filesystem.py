"""Tests for filesystem monitoring functionality."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from pokerops.monitoring.filesystem import argument, files, find


@pytest.fixture
def temp_file_structure(tmp_path):
    """Create a temporary file structure for testing.

    Structure:
        tmp_path/
        ├── file1.txt
        ├── file2.txt
        ├── subdir/
        │   ├── file3.txt
        │   └── nested/
        │       └── file4.txt
        └── old_file.txt
    """
    # Create files
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    old_file = tmp_path / "old_file.txt"

    file1.write_text("content1")
    file2.write_text("content2")
    old_file.write_text("old content")

    # Create subdirectory structure
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file3 = subdir / "file3.txt"
    file3.write_text("content3")

    nested = subdir / "nested"
    nested.mkdir()
    file4 = nested / "file4.txt"
    file4.write_text("content4")

    return {
        "root": tmp_path,
        "file1": file1,
        "file2": file2,
        "old_file": old_file,
        "file3": file3,
        "file4": file4,
    }


class TestArgument:
    """Tests for argument function."""

    def test_argument_with_value(self):
        """Test argument with a value."""
        result = argument("-mtime", "+7")
        assert result == "-mtime +7"

    def test_argument_with_none(self):
        """Test argument with None value."""
        result = argument("-mtime", None)
        assert result == ""

    def test_argument_with_empty_string(self):
        """Test argument with empty string."""
        result = argument("-mtime", "")
        assert result == ""


class TestFind:
    """Tests for find function."""

    def test_find_basic(self, temp_file_structure):
        """Test basic find without filters."""
        root = temp_file_structure["root"]
        error, result = find(root)

        assert error is None
        assert result is not None
        assert len(result) >= 5  # Should find all files and directories

    def test_find_with_maxdepth(self, temp_file_structure):
        """Test find with maxdepth argument."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["-maxdepth", "1"])

        assert error is None
        assert result is not None
        # Should only find items in root directory (less than all nested files)
        assert len(result) < 7

    def test_find_with_mtime(self, temp_file_structure):
        """Test find with mtime filter."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["-mtime", "-1"])

        assert error is None
        assert result is not None
        # Should find recently modified files (test files were just created)
        assert len(result) >= 4

    def test_find_with_type_file(self, temp_file_structure):
        """Test find with type filter for files only."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["-type", "f"])

        assert error is None
        assert result is not None
        # Should find only files, not directories
        assert len(result) == 5

    def test_find_with_multiple_arguments(self, temp_file_structure):
        """Test find with multiple arguments."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["-type", "f", "-name", "*.txt"])

        assert error is None
        assert result is not None
        # Should find all .txt files
        assert len(result) == 5

    def test_find_nonexistent_path(self, tmp_path):
        """Test find on non-existent path."""
        nonexistent = tmp_path / "nonexistent"
        error, result = find(nonexistent)

        assert error is not None
        assert result is None
        assert "find command failed" in error

    def test_find_with_invalid_argument(self, temp_file_structure):
        """Test find with invalid argument."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["--invalid-flag"])

        assert error is not None
        assert result is None
        assert "find command failed" in error

    def test_find_empty_directory(self, tmp_path):
        """Test find on empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        error, result = find(empty_dir)

        assert error is None
        assert result is not None
        # Should find at least the directory itself
        assert len(result) >= 1

    def test_find_returns_path_objects(self, temp_file_structure):
        """Test that find returns Path objects."""
        root = temp_file_structure["root"]
        error, result = find(root, arguments=["-type", "f"])

        assert error is None
        assert result is not None
        assert all(isinstance(p, Path) for p in result)

    @patch("subprocess.run")
    def test_find_handles_subprocess_error(self, mock_run, tmp_path):
        """Test find handles subprocess.CalledProcessError."""
        mock_run.side_effect = subprocess.CalledProcessError(1, ["find"], stderr="Permission denied")

        error, result = find(tmp_path)

        assert error is not None
        assert result is None
        assert "exit code 1" in error
        assert "Permission denied" in error

    @patch("subprocess.run")
    def test_find_handles_general_exception(self, mock_run, tmp_path):
        """Test find handles general exceptions."""
        mock_run.side_effect = Exception("Unexpected error")

        error, result = find(tmp_path)

        assert error is not None
        assert result is None
        assert "Error executing find" in error
        assert "Unexpected error" in error


class TestFiles:
    """Tests for files function."""

    def test_files_basic_output(self, temp_file_structure, capsys):
        """Test basic files function output."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test-location",
            environment="test-env",
            function="test-function",
            log_id="test-log",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Verify structure
        assert "filesystem" in output
        assert output["filesystem"]["path"] == str(root)
        assert output["filesystem"]["count"] >= 5
        assert len(output["filesystem"]["files"]) >= 5

        # Verify metadata
        assert output["fields"]["location"] == "test-location"
        assert output["fields"]["environment"] == "test-env"
        assert output["fields"]["function"] == "test-function"
        assert output["fields"]["log"]["description"] == "test-log"
        assert "@timestamp" in output
        assert "host" in output

    def test_files_with_mtime_filter(self, temp_file_structure, capsys):
        """Test files function with mtime filter."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test",
            environment="test",
            function="test",
            mtime="-1",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should find recent files
        assert output["filesystem"]["count"] >= 4
        assert output["filesystem"]["mtime"] == "-1"

    def test_files_with_ctime_filter(self, temp_file_structure, capsys):
        """Test files function with ctime filter."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test",
            environment="test",
            function="test",
            ctime="-1",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["filesystem"]["count"] >= 4
        assert output["filesystem"]["ctime"] == "-1"

    def test_files_with_both_filters(self, temp_file_structure, capsys):
        """Test files function with both mtime and ctime filters."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test",
            environment="test",
            function="test",
            mtime="-1",
            ctime="-1",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["filesystem"]["count"] >= 4
        assert output["filesystem"]["mtime"] == "-1"
        assert output["filesystem"]["ctime"] == "-1"

    def test_files_non_recursive(self, temp_file_structure, capsys):
        """Test files function with recursive=False."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test",
            environment="test",
            function="test",
            recursive=False,
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should only find files in root directory (maxdepth 1)
        # Note: maxdepth 1 includes the directory itself
        assert output["filesystem"]["count"] >= 3

    def test_files_default_parameters(self, temp_file_structure, capsys):
        """Test files function with default parameters."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="",
            environment="",
            function="",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should use default log_id
        assert output["fields"]["log"]["description"] == "filesystem-files"
        assert output["filesystem"]["mtime"] is None
        assert output["filesystem"]["ctime"] is None

    def test_files_json_format(self, temp_file_structure, capsys):
        """Test that output is valid JSON."""
        root = temp_file_structure["root"]

        files(
            path=str(root),
            location="test",
            environment="test",
            function="test",
        )

        captured = capsys.readouterr()

        # Should not raise JSONDecodeError
        output = json.loads(captured.out)

        # Verify structure types
        assert isinstance(output, dict)
        assert isinstance(output["filesystem"], dict)
        assert isinstance(output["filesystem"]["files"], list)
        assert isinstance(output["filesystem"]["count"], int)
        assert isinstance(output["fields"], dict)
        assert isinstance(output["host"], dict)

    def test_files_empty_directory(self, tmp_path, capsys):
        """Test files function on empty directory."""
        files(
            path=str(tmp_path),
            location="test",
            environment="test",
            function="test",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should find at least the directory itself
        assert output["filesystem"]["count"] >= 0
        assert isinstance(output["filesystem"]["files"], list)

    def test_files_handles_errors(self, capsys):
        """Test files function handles errors from find."""
        with pytest.raises(typer.Exit) as exc_info:
            files(
                path="/nonexistent/path/that/does/not/exist",
                location="test",
                environment="test",
                function="test",
            )

        assert exc_info.value.exit_code == 1

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should include error information
        assert "filesystem" in output
        assert "error" in output["filesystem"]
        assert output["filesystem"]["error"] is not None
        assert "find command failed" in output["filesystem"]["error"]

    def test_files_with_relative_path(self, temp_file_structure, capsys):
        """Test files function resolves relative paths."""
        root = temp_file_structure["root"]

        # Change to parent directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(root.parent)
            relative_path = root.name

            files(
                path=relative_path,
                location="test",
                environment="test",
                function="test",
            )

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            # Should successfully scan the directory
            assert output["filesystem"]["count"] >= 5
            assert "files" in output["filesystem"]
        finally:
            os.chdir(original_cwd)
