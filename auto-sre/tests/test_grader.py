"""Unit tests for the grader module."""

import pytest
from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import ConfigGrader, PortGrader, DependencyGrader


class TestConfigGrader:
    grader: ConfigGrader
    pm: ProcessManager

    def setup_method(self) -> None:
        self.grader = ConfigGrader()
        self.pm = ProcessManager()

    def test_full_credit_when_config_exists(self) -> None:
        fs = MockFilesystem()
        fs.set_overlay({"/etc/app/conf": MockFile(path="/etc/app/conf", content="OK")})
        reward, done, msg = self.grader.grade(fs, self.pm, [])
        assert reward == pytest.approx(0.989, abs=0.01)
        assert done is True

    def test_partial_credit_for_diagnostics(self) -> None:
        fs = MockFilesystem()
        reward, done, msg = self.grader.grade(fs, self.pm, ["ls /etc/app", "cat conf.bak"])
        assert 0 < reward < 1
        assert done is False

    def test_zero_when_nothing_done(self) -> None:
        fs = MockFilesystem()
        reward, done, msg = self.grader.grade(fs, self.pm, [])
        assert reward > 0
        assert reward < 0.2


class TestPortGrader:
    grader: PortGrader
    fs: MockFilesystem

    def setup_method(self) -> None:
        self.grader = PortGrader()
        self.fs = MockFilesystem()

    def test_full_credit_when_port_free(self) -> None:
        pm = ProcessManager()
        pm.load([MockProcess(pid=1, command="init")])
        reward, done, _ = self.grader.grade(self.fs, pm, [])
        assert reward == pytest.approx(0.989, abs=0.01)
        assert done is True

    def test_zero_when_port_occupied(self) -> None:
        pm = ProcessManager()
        pm.load([MockProcess(pid=512, command="rogue", port_bindings=[8080])])
        reward, done, _ = self.grader.grade(self.fs, pm, [])
        assert reward > 0
        assert reward < 0.2
        assert done is False

    def test_partial_credit_diagnostics(self) -> None:
        pm = ProcessManager()
        pm.load([MockProcess(pid=512, command="rogue", port_bindings=[8080])])
        reward, done, _ = self.grader.grade(self.fs, pm, ["ps aux"])
        assert 0 < reward < 1


class TestDependencyGrader:
    grader: DependencyGrader
    pm: ProcessManager

    def setup_method(self) -> None:
        self.grader = DependencyGrader()
        self.pm = ProcessManager()

    def test_full_credit_when_deps_installed(self) -> None:
        fs = MockFilesystem()
        fs.set_overlay({
            "/home/user/app/node_modules/.package-lock.json":
                MockFile(path="/home/user/app/node_modules/.package-lock.json", content="{}")
        })
        reward, done, _ = self.grader.grade(fs, self.pm, [])
        assert reward == pytest.approx(0.989, abs=0.01)
        assert done is True

    def test_zero_when_nothing_done(self) -> None:
        fs = MockFilesystem()
        reward, done, _ = self.grader.grade(fs, self.pm, [])
        assert reward > 0
        assert reward < 0.2
