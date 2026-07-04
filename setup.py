"""Build hook: bundle templates/, playbook/, examples/ into the wheel."""

from __future__ import annotations

from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = Path(__file__).parent
_KIT_DIRS = ("templates", "playbook", "examples")


class BuildPy(build_py):
    def run(self) -> None:
        super().run()
        build_lib = Path(self.build_lib)
        kit_root = build_lib / "launchpad" / "_kit"
        for name in _KIT_DIRS:
            src = ROOT / name
            dest = kit_root / name
            if src.is_dir():
                self.copy_tree(str(src), str(dest))


setup(cmdclass={"build_py": BuildPy})
