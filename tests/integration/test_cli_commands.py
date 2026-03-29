"""Integration tests for CLI commands."""

import subprocess
import sys


class TestCLICommands:
    """Tests for CLI commands."""

    def test_cli_help(self):
        """Test CLI help command."""
        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "File Organizer" in result.stdout

    def test_init_command(self, temp_dir, monkeypatch):
        """Test init command creates directories."""
        # Mock config dir to temp location
        monkeypatch.setenv("HOME", str(temp_dir))

        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "init"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_list_command_empty(self, temp_dir, monkeypatch):
        """Test list command with no profiles."""
        monkeypatch.setenv("HOME", str(temp_dir))

        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "list"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "No profiles" in result.stdout or "profiles" in result.stdout.lower()

    def test_ai_status_command(self):
        """Test AI status command."""
        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "ai", "status"],
            capture_output=True,
            text=True,
        )

        # Should succeed even if Ollama not installed
        assert result.returncode == 0
        assert "AI Status" in result.stdout or "Installed" in result.stdout


class TestCLIRunCommand:
    """Tests for the run command."""

    def test_run_nonexistent_profile(self):
        """Test run with non-existent profile."""
        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "run", "-p", "nonexistent"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "Error" in result.stderr

    def test_run_invalid_profile(self, temp_dir, monkeypatch):
        """Test run with invalid profile."""
        monkeypatch.setenv("HOME", str(temp_dir))

        from file_organizer.config.loader import ensure_config_dirs, get_profiles_dir

        ensure_config_dirs()
        profiles_dir = get_profiles_dir()
        profiles_dir.mkdir(parents=True, exist_ok=True)

        # Create invalid profile
        profile_file = profiles_dir / "invalid.yaml"
        profile_file.write_text("not: valid: yaml: [")

        result = subprocess.run(
            [sys.executable, "-m", "file_organizer.cli", "run", "-p", "invalid"],
            capture_output=True,
            text=True,
        )

        # Should fail due to invalid YAML
        assert result.returncode != 0
