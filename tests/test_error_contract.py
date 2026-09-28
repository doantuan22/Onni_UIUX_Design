"""Error contract: taxonomy, envelope, argument validation, internal-error guard (no traceback in public output)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _paths
from uiux import api, cli
from uiux.core import errors, schema

ROOT = _paths.PACKAGE_ROOT
CLI = str(ROOT / "scripts/uiux_cli.py")
ENVELOPE_KEYS = {"status", "error", "error_code", "category", "remediation"}


def run_cli(*args: str, env: dict | None = None) -> tuple[int, dict, str]:
    with tempfile.TemporaryDirectory() as cwd:
        result = subprocess.run([sys.executable, CLI, *args], capture_output=True, text=True, encoding="utf-8", cwd=cwd,
                                env={**os.environ, **(env or {})})
    return result.returncode, json.loads(result.stdout), result.stdout + result.stderr


def broken_validate_skill() -> dict:
    raise RuntimeError("secret detail /home/user/token=abc")


broken_validate_skill.__name__ = "validate_skill"  # dispatchable under the registered entrypoint name
BROKEN = mock.patch.dict(api._DISPATCH, {"validate_skill": broken_validate_skill})


def in_process(*args: str) -> tuple[int, dict, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(list(args))
    return code, json.loads(out.getvalue()), err.getvalue()


class TaxonomyTests(unittest.TestCase):
    data = errors.taxonomy()

    def test_categories_and_codes(self) -> None:
        self.assertEqual(set(self.data["categories"]), {"validation", "configuration", "package", "registry", "runtime",
                                                        "dependency", "internal", "unsupported"})
        for code, entry in self.data["codes"].items():
            with self.subTest(code=code):
                self.assertRegex(code, r"^[A-Z][A-Z_]+$")
                self.assertIn(entry["category"], self.data["categories"])
                self.assertTrue(entry["remediation"].strip())
                self.assertTrue(set(entry["scope"]) <= {"envelope", "result", "runtime-report"})

    def test_status_and_exit_codes_keep_the_0x_cli_contract(self) -> None:
        for name, category in self.data["categories"].items():
            expected = ("ERROR", 1) if name == "internal" else ("INVALID_CALL", 3)
            self.assertEqual((category["status"], category["exit_code"]), expected, name)

    def test_required_codes_are_registered(self) -> None:
        for code in ("INVALID_ARGUMENT", "INVALID_ARGUMENT_TYPE", "UNKNOWN_TOOL", "MISSING_REQUIRED_ARGUMENT",
                     "UNEXPECTED_ARGUMENT", "CONFIG_INVALID", "CONFIG_UNSUPPORTED", "MANIFEST_INVALID", "VERSION_MISMATCH",
                     "REGISTRY_INVALID", "PLAYWRIGHT_IMPORT_FAILURE", "PLAYWRIGHT_BROWSER_UNAVAILABLE",
                     "UNSUPPORTED_OPERATION", "INTERNAL_ERROR"):
            self.assertIn(code, self.data["codes"])

    def test_runtime_codes_emitted_by_the_runtime_are_registered(self) -> None:
        source = "".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "uiux/runtime").glob("*.py")))
        literals = set(re.findall(r"""['"]([A-Z]+(?:_[A-Z]+)+)['"]""", source))
        not_error_codes = {  # runtime states, result/scan statuses, environment variables and helper markers
            "NOT_DECLARED", "DECLARED_NOT_INSTALLED", "PACKAGE_AVAILABLE_BROWSER_MISSING", "NOT_AVAILABLE",
            "AVAILABLE_WITH_LIMITATIONS", "DRY_RUN", "INVALID_INPUT", "SCAN_FAILURE", "AXE_NOT",
            "PLAYWRIGHT_BROWSERS_PATH", "XDG_CACHE_HOME", "PROBE_JS", "LAYOUT_PROBE_JS"}
        codes = literals - not_error_codes
        self.assertTrue({"PLAYWRIGHT_IMPORT_FAILURE", "AXE_NOT_AVAILABLE", "BLANK_RENDER"} <= codes, codes)
        self.assertEqual(sorted(codes - set(self.data["codes"])), [])

    def test_unregistered_codes_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            errors.UiuxError("x", "NOT_A_REGISTERED_CODE")


class EnvelopeTests(unittest.TestCase):
    def assert_rejected(self, code: str, tool: str, params: object) -> errors.UiuxError:
        with self.assertRaises(api.ToolError) as caught:
            api.call_tool(tool, params)
        envelope = caught.exception.envelope()
        self.assertEqual(envelope["error_code"], code)
        self.assertEqual(envelope["status"], "INVALID_CALL")
        self.assertTrue(ENVELOPE_KEYS <= set(envelope))
        self.assertTrue(envelope["remediation"])
        self.assertIsInstance(caught.exception, ValueError)  # 0.x callers catch ValueError
        return caught.exception

    def test_known_validation_error(self) -> None:
        exc = self.assert_rejected("INVALID_ARGUMENT", "resolve_capabilities", {"profile": {}})
        self.assertIn("domain, brand_attributes and contexts are required", exc.message)

    def test_unknown_tool(self) -> None:
        self.assertEqual(self.assert_rejected("UNKNOWN_TOOL", "nope", {}).message, "unknown tool: nope")

    def test_missing_argument(self) -> None:
        exc = self.assert_rejected("MISSING_REQUIRED_ARGUMENT", "resolve_capabilities", {})
        self.assertEqual(exc.message, "resolve_capabilities: missing required parameters: profile")

    def test_unexpected_argument(self) -> None:
        exc = self.assert_rejected("UNEXPECTED_ARGUMENT", "retrieve_knowledge", {"collection": "styles", "zzz": 1})
        self.assertEqual(exc.message, "retrieve_knowledge: unknown parameters: zzz")

    def test_wrong_types(self) -> None:
        cases = [("retrieve_knowledge", {"ids": "style.swiss"}), ("retrieve_knowledge", {"include_content": "yes"}),
                 ("retrieve_knowledge", {"ids": ["style.swiss", 3]}), ("analyze_design_quality", {"project": ".", "visual_intensity": True}),
                 ("analyze_design_quality", {"project": ".", "visual_intensity": 2.5}), ("run_runtime", {"request": [], "project": "."}),
                 ("resolve_technology", {"capabilities": None}), ("detect_runtime", {"project": 1})]
        for tool, params in cases:
            with self.subTest(tool=tool, params=params):
                self.assert_rejected("INVALID_ARGUMENT_TYPE", tool, params)
        self.assert_rejected("INVALID_ARGUMENT_TYPE", "validate_skill", ["not", "an", "object"])

    def test_enum_and_nullable(self) -> None:
        self.assert_rejected("INVALID_ARGUMENT", "retrieve_knowledge", {"collection": "fonts"})
        self.assert_rejected("INVALID_ARGUMENT", "run_evals", {"suites": ["knowledge", "made-up"]})
        self.assertGreater(api.call_tool("retrieve_knowledge", {"collection": None, "text": None, "ids": None})["count"], 200)

    def test_lower_layer_error_keeps_message_and_code(self) -> None:
        exc = self.assert_rejected("INVALID_ARGUMENT", "retrieve_knowledge", {"ids": ["style.nope"]})
        self.assertEqual(exc.message, "unknown knowledge ids: style.nope")

    def test_internal_exception_becomes_internal_error_without_details(self) -> None:
        with BROKEN:
            with self.assertRaises(errors.InternalError) as caught:
                api.call_tool("validate_skill", {})
        envelope = caught.exception.envelope()
        self.assertEqual((envelope["status"], envelope["error_code"], envelope["category"]), ("ERROR", "INTERNAL_ERROR", "internal"))
        self.assertNotIn("secret", json.dumps(envelope))
        self.assertEqual(envelope["details"], {"exception_type": "RuntimeError"})
        self.assertIsNone(caught.exception.__cause__)


class CliEnvelopeTests(unittest.TestCase):
    def test_invalid_calls_keep_status_error_and_exit_3(self) -> None:
        cases = {("call", "nope"): "UNKNOWN_TOOL",
                 ("call", "resolve_capabilities", "--params", "{}"): "MISSING_REQUIRED_ARGUMENT",
                 ("call", "retrieve_knowledge", "--params", '{"ids": "x"}'): "INVALID_ARGUMENT_TYPE",
                 ("call", "retrieve_knowledge", "--params", "[1]"): "INVALID_ARGUMENT_TYPE",
                 ("call", "retrieve_knowledge", "--params", "{bad json"): "INVALID_ARGUMENT",
                 ("call", "retrieve_knowledge", "--params", "@does-not-exist.json"): "FILESYSTEM_ERROR"}
        for args, code in cases.items():
            with self.subTest(args=args):
                exit_code, data, output = run_cli(*args)
                self.assertEqual(exit_code, 3)
                self.assertEqual((data["status"], data["error_code"]), ("INVALID_CALL", code))
                self.assertIsInstance(data["error"], str)
                self.assertTrue(data["remediation"])
                self.assertNotIn("Traceback", output)

    def test_config_errors_are_configuration_category(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            unsupported = Path(temporary, "a.json")
            unsupported.write_text('{"schema_version": 1, "dependency_policy": {"auto_install": true}}', encoding="utf-8")
            invalid = Path(temporary, "b.json")
            invalid.write_text('{"schema_version": 1, "paths": {"docs": "../outside"}}', encoding="utf-8")
            for path, code in ((unsupported, "CONFIG_UNSUPPORTED"), (invalid, "CONFIG_INVALID")):
                with self.subTest(code=code):
                    exit_code, data, output = run_cli("call", "validate_skill", env={"UIUX_CONFIG": str(path)})
                    self.assertEqual((exit_code, data["error_code"], data["category"]), (3, code, "configuration"))
                    self.assertNotIn("Traceback", output)

    def test_internal_error_has_no_traceback_unless_debug(self) -> None:
        with BROKEN:
            with mock.patch.dict(os.environ, {"UIUX_DEBUG": "0"}):
                code, data, stderr = in_process("call", "validate_skill")
            self.assertEqual((code, data["status"], data["error_code"]), (1, "ERROR", "INTERNAL_ERROR"))
            self.assertNotIn("secret", json.dumps(data))
            self.assertNotIn("Traceback", json.dumps(data) + stderr)
            with mock.patch.dict(os.environ, {"UIUX_DEBUG": "1"}):
                code, data, stderr = in_process("call", "validate_skill")
            self.assertEqual(code, 1)
            self.assertNotIn("Traceback", json.dumps(data))
            self.assertIn("Traceback", stderr)
            self.assertIn("secret detail", stderr)


class SchemaValidatorTests(unittest.TestCase):
    SCHEMA = {"type": "object", "required": ["a"], "additionalProperties": False, "properties": {
        "a": {"type": "integer"}, "b": {"type": "number"}, "c": {"type": ["string", "null"], "enum": ["x", "y", None]},
        "d": {"type": "array", "items": {"type": "boolean"}}, "e": {"type": "object"}}}

    def code(self, params: object) -> str | None:
        try:
            schema.validate_arguments("t", self.SCHEMA, params)
        except errors.UiuxError as exc:
            return exc.code
        return None

    def test_types(self) -> None:
        self.assertIsNone(self.code({"a": 1, "b": 2, "c": None, "d": [True], "e": {}}))
        self.assertIsNone(self.code({"a": 1, "b": 2.5, "c": "x"}))
        self.assertEqual(self.code({"a": True}), "INVALID_ARGUMENT_TYPE")   # bool is not an integer
        self.assertEqual(self.code({"a": 1.0}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self.code({"a": 1, "b": False}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self.code({"a": 1, "d": [1]}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self.code({"a": 1, "e": []}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self.code({"a": None}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self.code({"a": 1, "c": "z"}), "INVALID_ARGUMENT")
        self.assertEqual(self.code({}), "MISSING_REQUIRED_ARGUMENT")
        self.assertEqual(self.code({"a": 1, "z": 1}), "UNEXPECTED_ARGUMENT")
        self.assertEqual(self.code("x"), "INVALID_ARGUMENT_TYPE")

    def test_first_error_is_deterministic(self) -> None:
        self.assertEqual(self.code({"z": 1}), "MISSING_REQUIRED_ARGUMENT")
        self.assertEqual(self.code({"a": "x", "z": 1}), "UNEXPECTED_ARGUMENT")

    def test_schema_checker_rejects_unsupported_keywords(self) -> None:
        self.assertEqual(schema.check_schema(self.SCHEMA), [])
        self.assertTrue(schema.check_schema({"type": "object", "properties": {"a": {"type": "string", "format": "uri"}},
                                             "additionalProperties": False}))
        self.assertTrue(schema.check_schema({"type": "object", "properties": {}}))  # additionalProperties false required
        self.assertTrue(schema.check_schema({"type": "object", "properties": {"a": {"type": "date"}}, "additionalProperties": False}))

    def test_nested_object_and_array_validation(self) -> None:
        nested = {"type": "object", "additionalProperties": False, "properties": {
            "profile": {"type": "object", "additionalProperties": False, "required": ["limit"],
                        "properties": {"limit": {"type": "integer", "minimum": 1},
                                       "tags": {"type": "array", "items": {"type": "string"}}}}}}
        self.assertEqual(schema.check_schema(nested), [])
        self.assertEqual(self._nested_code(nested, {"profile": {"limit": 2, "tags": ["a"]}}), None)
        self.assertEqual(self._nested_code(nested, {"profile": {}}), "MISSING_REQUIRED_ARGUMENT")
        self.assertEqual(self._nested_code(nested, {"profile": {"limit": 0}}), "INVALID_ARGUMENT")
        self.assertEqual(self._nested_code(nested, {"profile": {"limit": True}}), "INVALID_ARGUMENT_TYPE")
        self.assertEqual(self._nested_code(nested, {"profile": {"limit": 1, "extra": 1}}), "UNEXPECTED_ARGUMENT")

    @staticmethod
    def _nested_code(nested: dict, params: dict) -> str | None:
        try:
            schema.validate_arguments("nested", nested, params)
        except errors.UiuxError as exc:
            return exc.code
        return None


if __name__ == "__main__":
    unittest.main()
