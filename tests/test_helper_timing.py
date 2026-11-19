import asyncio
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
from urllib import error


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("helper_timing", ROOT / "assets/helper_timing.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
HelperTiming = module.HelperTiming


class Clock:
    def __init__(self):
        self.value = 0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def read_trace(output, diagnostics):
    return json.loads((output / diagnostics["trace_ref"]).read_text())


class TimingTests(unittest.TestCase):
    def test_nested_work_and_wait_have_distinct_durations_and_parents(self):
        with tempfile.TemporaryDirectory() as directory:
            output, clock = Path(directory), Clock()
            trace = HelperTiming("book_appointment", output_dir=output, clock=clock)
            with trace.span("select_customer", kind="phase"):
                clock.advance(1)
                with trace.span("search_customer", kind="http") as span:
                    clock.advance(2)
                    span.annotate(http_status=200)
                with trace.span("wait_for_matching_result", kind="wait") as span:
                    clock.advance(0.5)
                    span.annotate(attempts=3)
            diag = trace.finish()
            records = read_trace(output, diag)["spans"]
            root, phase, request, wait = records
            self.assertEqual(diag["elapsed_ms"], 3500)
            self.assertEqual(diag["phase_ms"], {"select_customer": 3500})
            self.assertEqual(phase["parent_span_id"], root["span_id"])
            self.assertEqual(request["parent_span_id"], phase["span_id"])
            self.assertEqual(wait["parent_span_id"], phase["span_id"])
            self.assertEqual((request["start_ms"], request["duration_ms"]), (1000, 2000))
            self.assertEqual((wait["duration_ms"], wait["attempts"]), (500, 3))
            self.assertEqual(request["http_status"], 200)
            self.assertEqual(stat.S_IMODE((output / diag["trace_ref"]).stat().st_mode), 0o600)
            self.assertNotIn("spans", diag)

    def test_repeated_subtasks_keep_individual_records(self):
        with tempfile.TemporaryDirectory() as directory:
            clock = Clock()
            trace = HelperTiming("lookup", output_dir=directory, clock=clock)
            for _ in range(3):
                with trace.span("search", kind="phase"):
                    clock.advance(0.1)
            diag = trace.finish()
            records = read_trace(Path(directory), diag)["spans"]
            self.assertEqual(diag["phase_ms"], {"search": 300})
            self.assertEqual(len({s["span_id"] for s in records}), 4)

    def test_normal_empty_result_is_success_with_a_distinguishing_code(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = HelperTiming("search_customer", output_dir=directory)
            with trace.span("search", kind="phase"):
                pass
            diag = trace.finish("done", "no_match")
            self.assertEqual(diag["code"], "no_match")
            self.assertNotIn("phase", diag)
            self.assertEqual(read_trace(Path(directory), diag)["spans"][0]["outcome"], "ok")

    def test_timeout_preserves_exception_and_failed_subtask_without_raw_text(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = HelperTiming("lookup", output_dir=directory)
            failure = TimeoutError("private customer data and token=secret")
            with self.assertRaises(TimeoutError) as caught:
                with trace.span("lookup_customer", kind="phase"):
                    with trace.span("customer_request", kind="http"):
                        raise failure
            self.assertIs(caught.exception, failure)
            diag = trace.finish("blocked", "api_unavailable")
            payload = read_trace(Path(directory), diag)
            self.assertEqual(diag["phase"], "customer_request")
            self.assertEqual(payload["spans"][-1]["outcome"], "timeout")
            self.assertNotIn("secret", json.dumps(payload))
            self.assertNotIn("private", json.dumps(payload))

    def test_fallback_is_a_separate_step_with_safe_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = HelperTiming("verify_record", output_dir=directory)
            with trace.span("read_exact_record", kind="http") as span:
                span.annotate(outcome="blocked", code="record_read_unavailable", http_status=503)
            with trace.span("page_readback_fallback"):
                pass
            diag = trace.finish()
            records = read_trace(Path(directory), diag)["spans"]
            self.assertEqual(records[1]["code"], "record_read_unavailable")
            self.assertEqual(records[2]["name"], "page_readback_fallback")
            self.assertEqual(records[0]["outcome"], "ok")

    def test_storage_failure_does_not_repeat_business_action_or_change_result(self):
        with tempfile.TemporaryDirectory() as directory:
            unwritable = Path(directory) / "regular-file"
            unwritable.write_text("not a directory")
            trace = HelperTiming("submit_record", output_dir=unwritable)
            submissions = []
            with trace.span("submit", kind="phase"):
                submissions.append("once")
                result = {"status": "done", "summary": "Saved and verified."}
            diag = trace.finish(result["status"])
            self.assertEqual(submissions, ["once"])
            self.assertEqual(result, {"status": "done", "summary": "Saved and verified."})
            self.assertTrue(diag["trace_write_failed"])
            self.assertNotIn("trace_ref", diag)

    def test_storage_failure_never_masks_original_business_exception(self):
        trace = HelperTiming("submit_record", output_dir="unused")
        original = RuntimeError("original business failure")
        with patch.object(trace, "_write", side_effect=OSError("log sink failed")):
            with self.assertRaises(RuntimeError) as caught:
                try:
                    with trace.span("submit", kind="phase"):
                        raise original
                finally:
                    diag = trace.finish("failed", "uncertain_outcome")
        self.assertIs(caught.exception, original)
        self.assertTrue(diag["trace_write_failed"])

    def test_spans_and_output_are_bounded_and_truncation_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = HelperTiming("lookup", output_dir=directory, max_spans=2)
            for _ in range(20):
                with trace.span("poll", kind="wait"):
                    pass
            diag = trace.finish()
            payload = read_trace(Path(directory), diag)
            self.assertEqual(diag["dropped_spans"], 18)
            self.assertEqual(len(payload["spans"]), 3)
            self.assertEqual(payload["dropped_spans"], 18)

    def test_retention_only_removes_owned_trace_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            old = output / ("trace-" + "a" * 32 + ".json")
            old.write_text("{}")
            os.utime(old, (time.time() - 100, time.time() - 100))
            unrelated = output / "customer-report.json"
            unrelated.write_text("keep")
            folder = output / ("trace-" + "b" * 32 + ".json")
            folder.mkdir()
            link = output / ("trace-" + "c" * 32 + ".json")
            link.symlink_to(unrelated)
            for _ in range(4):
                HelperTiming("lookup", output_dir=output, keep_runs=2, retention_seconds=10).finish()
            files = [p for p in output.iterdir() if p.is_file() and not p.is_symlink() and re.fullmatch(r"trace-[0-9a-f]{32}\.json", p.name)]
            self.assertEqual(len(files), 2)
            self.assertFalse(old.exists())
            self.assertTrue(folder.is_dir())
            self.assertTrue(link.is_symlink())
            self.assertEqual(unrelated.read_text(), "keep")

    def test_finish_is_idempotent_and_does_not_write_twice(self):
        trace = HelperTiming("lookup", output_dir="unused")
        with patch.object(trace, "_write", return_value="trace.json") as write:
            first = trace.finish("done")
            second = trace.finish("blocked", "should_not_replace_result")
        self.assertEqual(first, second)
        write.assert_called_once()

    def test_unclosed_spans_are_reported_as_unfinished(self):
        trace = HelperTiming("lookup")
        with trace.span("still_running"):
            diag = trace.finish()
        self.assertEqual(diag["unfinished_spans"], 1)

    def test_async_siblings_keep_their_own_parent_context(self):
        async def scenario(trace):
            async def worker(name):
                with trace.span(name):
                    await asyncio.sleep(0)
                    with trace.span(name + "_request", kind="http"):
                        await asyncio.sleep(0)
            with trace.span("parallel_lookup", kind="phase"):
                await asyncio.gather(worker("left"), worker("right"))

        with tempfile.TemporaryDirectory() as directory:
            trace = HelperTiming("lookup", output_dir=directory)
            asyncio.run(scenario(trace))
            payload = read_trace(Path(directory), trace.finish())
            spans = {s["name"]: s for s in payload["spans"]}
            for name in ["left", "right"]:
                self.assertEqual(spans[name]["parent_span_id"], spans["parallel_lookup"]["span_id"])
                self.assertEqual(spans[name + "_request"]["parent_span_id"], spans[name]["span_id"])


class AuthoringExampleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        namespace = {"__file__": str(Path(self.temp.name) / "helpers" / "lookup_customer.py")}
        runtime = types.ModuleType("vida_helper_runtime")
        runtime.computer_function = lambda **metadata: lambda fn: fn
        runtime.managed_secret = lambda secret_id: "private-test-secret"
        source = re.search(r"```python\n(.*?)```", (ROOT / "references/helper-authoring.md").read_text(), re.S).group(1)
        with patch.dict(sys.modules, {"helper_timing": module, "vida_helper_runtime": runtime}):
            exec(compile(source, "authoring-example.py", "exec"), namespace)
        self.lookup = namespace["lookup_customer"]
        self.output = Path(self.temp.name) / "outputs" / "helper-timing"

    def test_success_keeps_nested_request_and_parse_timings_outside_compact_result(self):
        @contextmanager
        def response(*args, **kwargs):
            yield types.SimpleNamespace(status=200, read=lambda: b'{"id":"example-id","name":"Private Caller"}')
        with patch("urllib.request.urlopen", side_effect=response):
            result = self.lookup("example-id")
        self.assertEqual(result["status"], "done")
        diag = result["result"]["diagnostics"]
        payload = read_trace(self.output, diag)
        self.assertIn("customer_lookup", diag["phase_ms"])
        self.assertTrue({"customer_request", "parse_response"}.issubset({s["name"] for s in payload["spans"]}))
        self.assertNotIn("Private Caller", json.dumps(payload))
        self.assertNotIn("private-test-secret", json.dumps(payload))
        self.assertNotIn("spans", diag)

    def test_early_validation_return_includes_diagnostics_without_network(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Must not request")):
            result = self.lookup("")
        self.assertEqual(result["reason"], "invalid_customer_id")
        self.assertEqual(result["result"]["diagnostics"]["phase"], "validate_arguments")
        self.assertIn("trace_ref", result["result"]["diagnostics"])

    def test_http_and_timeout_failures_keep_codes_and_never_log_exception_text(self):
        cases = [(error.HTTPError("https://private.invalid?token=secret", 401, "private exception", {}, None), "authentication_required"),
                 (TimeoutError("private exception"), "api_unavailable")]
        for failure, reason in cases:
            with self.subTest(reason=reason), patch("urllib.request.urlopen", side_effect=failure):
                result = self.lookup("private-record-id")
            self.assertEqual(result["reason"], reason)
            diag = result["result"]["diagnostics"]
            self.assertEqual(diag["phase"], "customer_request")
            text = (self.output / diag["trace_ref"]).read_text()
            self.assertNotIn("private", text)
            self.assertNotIn("secret", text)

    def test_malformed_response_identifies_parse_subtask(self):
        @contextmanager
        def response(*args, **kwargs):
            yield types.SimpleNamespace(status=200, read=lambda: b'not json')
        with patch("urllib.request.urlopen", side_effect=response):
            result = self.lookup("example-id")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["result"]["diagnostics"]["phase"], "parse_response")


if __name__ == "__main__":
    unittest.main()
