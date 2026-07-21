#!/usr/bin/env python3
"""Regression harness for Learning Tutor Hooks, CLI helpers, and Agent link.

Does not run a live Cursor Agent chat. Uses temporary HOME directories so the
real ~/.cursor/learning profile is never touched.

Usage (from repo root):
  python3 scripts/test_hooks_agents.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "hooks"
CAPTURE = HOOKS / "capture_learning.py"
INJECT = HOOKS / "inject_profile.py"
AGENT = ROOT / "agents" / "study-researcher.md"
STUDY_DEEP = ROOT / "skills" / "study-deep" / "SKILL.md"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)

if str(HOOKS) not in sys.path:
    sys.path.insert(0, str(HOOKS))


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_lib_with_home(home: Path):
    """Load lib_profile with LEARNING paths under a fake HOME."""
    for name in list(sys.modules):
        if name == "learning" or name.startswith("learning."):
            del sys.modules[name]
    with mock.patch.dict(os.environ, {"HOME": str(home)}):
        lib = load_module(HOOKS / "lib_profile.py", f"lib_profile_{home.name}_{id(home)}")
        lib.rebind_home(home)
        return lib


class WantRegexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.capture = load_module(CAPTURE, "capture_learning_under_test")

    def test_valid_marker_with_note(self) -> None:
        text = '<!-- LEARNING-WANT topic="Docker" note="for deploy" -->'
        matches = list(self.capture.WANT_RE.finditer(text))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].group("topic"), "Docker")
        self.assertEqual(matches[0].group("note"), "for deploy")

    def test_valid_marker_without_note(self) -> None:
        text = 'LEARNING-WANT topic="HTTP keep-alive"'
        matches = list(self.capture.WANT_RE.finditer(text))
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].group("topic"), "HTTP keep-alive")
        self.assertIsNone(matches[0].group("note"))

    def test_empty_topic_skipped_by_iterator(self) -> None:
        text = '<!-- LEARNING-WANT topic="" note="x" -->'
        self.assertEqual(list(self.capture.iter_want_markers(text)), [])

    def test_empty_then_valid_keeps_valid(self) -> None:
        text = (
            '<!-- LEARNING-WANT topic="" note="bad" -->\n'
            '<!-- LEARNING-WANT topic="Docker" note="ok" -->'
        )
        self.assertEqual(
            list(self.capture.iter_want_markers(text)),
            [("Docker", "ok")],
        )

    def test_malformed_missing_topic_ignored(self) -> None:
        text = "<!-- LEARNING-WANT note=\"only note\" -->"
        self.assertEqual(list(self.capture.WANT_RE.finditer(text)), [])

    def test_malformed_single_quotes_ignored(self) -> None:
        text = "<!-- LEARNING-WANT topic='Docker' -->"
        self.assertEqual(list(self.capture.WANT_RE.finditer(text)), [])


class HookIoTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hook_io = load_module(HOOKS / "hook_io.py", "hook_io_under_test")

    def test_official_after_agent_response_text_field(self) -> None:
        body = 'hi <!-- LEARNING-WANT topic="Docker" -->'
        data = {"text": body}
        self.assertEqual(
            self.hook_io.extract_response_text(data, b""),
            body,
        )

    def test_compat_response_key(self) -> None:
        data = {"response": 'LEARNING-WANT topic="API"'}
        self.assertIn("API", self.hook_io.extract_response_text(data, b""))

    def test_non_json_passthrough(self) -> None:
        raw = b'plain LEARNING-WANT topic="HTTP"'
        self.assertEqual(self.hook_io.extract_response_text(None, raw), raw.decode())

    def test_workspace_roots_extraction(self) -> None:
        roots = self.hook_io.workspace_roots_from_payload(
            {"workspace_roots": ["/tmp/a", 1, ""]}
        )
        self.assertEqual(roots, ["/tmp/a"])


class CaptureHookSubprocessTests(unittest.TestCase):
    def _run(self, home: Path, stdin: bytes, cwd: Path | None = None) -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(home), "PYTHONPATH": ""}
        return subprocess.run(
            [sys.executable, str(CAPTURE)],
            input=stdin,
            cwd=str(cwd or ROOT),
            env=env,
            capture_output=True,
            check=False,
        )

    def test_official_payload_writes_want(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            payload = json.dumps(
                {
                    "text": (
                        "Queued.\n"
                        '<!-- LEARNING-WANT topic="Docker Compose" note="deploy" -->'
                    )
                }
            ).encode()
            result = self._run(home, payload)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            out = json.loads(result.stdout.decode())
            self.assertTrue(out.get("continue"))
            profile = (home / ".cursor" / "learning" / "profile.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Docker Compose", profile)
            self.assertIn("[ ]", profile)

    def test_empty_topic_skipped_with_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            payload = json.dumps(
                {
                    "text": (
                        '<!-- LEARNING-WANT topic="" note="bad" -->\n'
                        '<!-- LEARNING-WANT topic="HTTP" -->'
                    )
                }
            ).encode()
            result = self._run(home, payload)
            self.assertEqual(result.returncode, 0)
            out = json.loads(result.stdout.decode())
            self.assertTrue(out.get("continue"))
            stderr = result.stderr.decode()
            self.assertIn("empty topic", stderr)
            profile = (home / ".cursor" / "learning" / "profile.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("HTTP", profile)
            self.assertNotIn("- [ ] bad", profile)

    def test_no_marker_still_fail_open_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self._run(home, json.dumps({"text": "ordinary answer"}).encode())
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout.decode()), {"continue": True})


class InjectHookSubprocessTests(unittest.TestCase):
    def _run(self, home: Path, cwd: Path, stdin: bytes = b"{}") -> subprocess.CompletedProcess:
        env = {**os.environ, "HOME": str(home), "PYTHONPATH": ""}
        return subprocess.run(
            [sys.executable, str(INJECT)],
            input=stdin,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            check=False,
        )

    def test_session_start_installs_cli_and_emits_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            home.mkdir()
            workspace = base / "workspace"
            project = workspace / ".cursor" / "learning"
            project.mkdir(parents=True)
            project.joinpath("project.md").write_text(
                "# Learning Tutor — project learning sheet\n\n## Stack\n\n- Next.js\n",
                encoding="utf-8",
            )
            learning = home / ".cursor" / "learning"
            learning.mkdir(parents=True)
            learning.joinpath("profile.md").write_text(
                "# Learning profile (global)\n\n## Meta\n"
                "- Overall level: intermediate\n"
                "- Current focus: backend\n\n"
                "## Study queue\n\n- [ ] Docker\n\n## Covered\n\n_None yet._\n",
                encoding="utf-8",
            )

            result = self._run(home, workspace)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            out = json.loads(result.stdout.decode())
            self.assertTrue(out.get("continue"))
            ctx = out.get("additional_context", "")
            self.assertIn("LEARNING-PROFILE", ctx)
            self.assertIn("Docker", ctx)
            self.assertIn("LEARNING-PROJECT", ctx)
            self.assertIn("Next.js", ctx)
            self.assertTrue((learning / "cli.py").is_file())
            self.assertTrue((learning / "lib_profile.py").is_file())

    def test_session_start_uses_workspace_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            home.mkdir()
            # Process cwd is empty; sheet lives only under workspace_roots
            empty_cwd = base / "empty_cwd"
            empty_cwd.mkdir()
            workspace = base / "real_workspace"
            sheet_dir = workspace / ".cursor" / "learning"
            sheet_dir.mkdir(parents=True)
            sheet_dir.joinpath("project.md").write_text(
                "# Learning Tutor — project learning sheet\n\n## Stack\n\n- Prisma\n",
                encoding="utf-8",
            )
            payload = json.dumps(
                {
                    "session_id": "t",
                    "is_background_agent": False,
                    "composer_mode": "agent",
                    "workspace_roots": [str(workspace)],
                }
            ).encode()
            result = self._run(home, empty_cwd, stdin=payload)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            ctx = json.loads(result.stdout.decode()).get("additional_context", "")
            self.assertIn("Prisma", ctx)

    def test_session_start_empty_profile_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            home.mkdir()
            workspace = base / "ws"
            workspace.mkdir()
            result = self._run(home, workspace)
            self.assertEqual(result.returncode, 0)
            out = json.loads(result.stdout.decode())
            self.assertIn("profile is still empty", out.get("additional_context", ""))

    def test_session_start_fail_open_on_broken_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "ws"
            workspace.mkdir()
            bad_home = base / "not_a_dir"
            bad_home.write_text("x", encoding="utf-8")
            result = self._run(bad_home, workspace)
            self.assertEqual(result.returncode, 0)
            out = json.loads(result.stdout.decode())
            self.assertTrue(out.get("continue"))
            self.assertIn("learning-tutor:", result.stderr.decode())


class LibProfileTempHomeTests(unittest.TestCase):
    def test_add_want_and_project_sync_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            project_root = Path(tmp) / "proj"
            project_root.mkdir()
            lib = load_lib_with_home(home)
            msg = lib.add_want("Docker", "for deploy")
            self.assertIn("Saved to profile (queue)", msg)
            profile = lib.read_profile()
            self.assertIn("Docker", profile)

            updated = lib.project_sync(
                stack="Next.js;Prisma",
                candidates="App Router;Prisma migrations",
                cwd=str(project_root),
            )
            self.assertIn("project.md", updated)
            shown = lib.project_show(str(project_root))
            self.assertIn("Next.js", shown)
            self.assertIn("App Router", shown)

    def test_resolve_project_root_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            explicit = Path(tmp) / "explicit"
            via_roots = Path(tmp) / "via_roots"
            explicit.mkdir()
            via_roots.mkdir()
            lib = load_lib_with_home(home)
            root = lib.resolve_project_root(
                cwd=str(explicit),
                workspace_roots=[str(via_roots)],
            )
            self.assertEqual(root, explicit.resolve())
            root2 = lib.resolve_project_root(workspace_roots=[str(via_roots)])
            self.assertEqual(root2, via_roots.resolve())

    def test_find_project_sheet_ancestor_walk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            root = Path(tmp) / "repo"
            nested = root / "apps" / "web"
            nested.mkdir(parents=True)
            sheet = root / ".cursor" / "learning" / "project.md"
            sheet.parent.mkdir(parents=True)
            sheet.write_text("# sheet\n", encoding="utf-8")
            lib = load_lib_with_home(home)
            found = lib.find_project_sheet(nested, walk_ancestors=True)
            self.assertEqual(found.resolve(), sheet.resolve())
            missing = lib.find_project_sheet(nested, walk_ancestors=False)
            self.assertIsNone(missing)

    def test_truncate_for_inject(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            home.mkdir(exist_ok=True)
            lib = load_lib_with_home(home)
            short = lib.truncate_for_inject("abc", max_chars=10)
            self.assertEqual(short, "abc")
            long = "x" * 5000
            out = lib.truncate_for_inject(long, max_chars=1000)
            self.assertLess(len(out), len(long))
            self.assertIn("...", out)

    def test_install_cli_copies_learning_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            lib = load_lib_with_home(home)
            lib.install_cli(HOOKS)
            learning = home / ".cursor" / "learning"
            self.assertTrue((learning / "cli.py").is_file())
            self.assertTrue((learning / "lib_profile.py").is_file())
            self.assertTrue((learning / "learning" / "__init__.py").is_file())
            self.assertTrue((learning / "learning" / "profile.py").is_file())
            result = subprocess.run(
                [sys.executable, str(learning / "cli.py"), "want", "--topic", "Docker"],
                env={**os.environ, "HOME": str(home), "PYTHONPATH": ""},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Saved to profile (queue)", result.stdout)
            self.assertIn("Docker", (learning / "profile.md").read_text(encoding="utf-8"))


class AgentLinkTests(unittest.TestCase):
    def test_agent_frontmatter_and_study_deep_reference(self) -> None:
        text = AGENT.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(text)
        self.assertIsNotNone(match)
        fm = match.group(1)
        self.assertRegex(fm, r"(?m)^name:\s*study-researcher\s*$")
        self.assertIn("description:", fm)
        self.assertRegex(fm, r"(?m)^model:\s*inherit\s*$")
        self.assertRegex(fm, r"(?m)^readonly:\s*true\s*$")

        deep = STUDY_DEEP.read_text(encoding="utf-8")
        self.assertIn("study-researcher", deep)


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
