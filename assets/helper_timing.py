"""Copy into an owning skill's helpers/; standard library only, no business I/O.

Names and codes must be static labels, never caller data or exception messages.
Use one instance per invocation, including concurrent async subtasks. Each span's
duration includes its children; overlapping spans must not be summed.
"""

from contextvars import ContextVar
from pathlib import Path
import json
import re
import time
import uuid


_LABEL = re.compile(r"[a-z][a-z0-9_.-]{0,63}\Z")
_TRACE_FILE = re.compile(r"trace-[0-9a-f]{32}\.json\Z")
_OUTCOMES = {"ok", "error", "timeout", "blocked", "need_user", "unfinished"}
_KINDS = {"phase", "step", "browser", "http", "wait", "sleep", "model"}


def _label(value, fallback):
    return value if isinstance(value, str) and _LABEL.fullmatch(value) else fallback


def _ms(seconds):
    return max(0, round(seconds * 1000))


class _Span:
    def __init__(self, trace, name, kind):
        self.trace, self.name, self.kind = trace, name, kind
        self.data = None
        self.token = None

    def __enter__(self):
        started = time.perf_counter()
        trace = self.trace
        if not trace._finished:
            if len(trace._spans) < trace.max_spans:
                self.data = {
                    "span_id": uuid.uuid4().hex[:16],
                    "parent_span_id": trace._parent.get(),
                    "name": _label(self.name, "step"),
                    "kind": self.kind if self.kind in _KINDS else "step",
                    "start_ms": _ms(trace.clock() - trace.started),
                    "outcome": "ok",
                }
                self.started = trace.clock()
                trace._spans.append(self.data)
                self.token = trace._parent.set(self.data["span_id"])
            else:
                trace._dropped += 1
        trace._overhead += time.perf_counter() - started
        return self

    def annotate(self, *, outcome=None, code=None, http_status=None, attempts=None):
        """Only bounded diagnostic fields; never pass arbitrary request metadata."""
        started = time.perf_counter()
        if self.data is None or "duration_ms" in self.data:
            return
        if outcome in _OUTCOMES:
            self.data["outcome"] = outcome
        if code is not None:
            self.data["code"] = _label(code, "operation_error")
        if type(http_status) is int and 100 <= http_status <= 599:
            self.data["http_status"] = http_status
        if type(attempts) is int and 0 <= attempts <= 1_000_000:
            self.data["attempts"] = attempts
        self.trace._overhead += time.perf_counter() - started

    def __exit__(self, exc_type, exc, traceback):
        started = time.perf_counter()
        trace = self.trace
        try:
            if self.data is not None and "duration_ms" not in self.data:
                self.data["duration_ms"] = _ms(trace.clock() - self.started)
                if exc_type is not None:
                    self.data["outcome"] = "timeout" if isinstance(exc, TimeoutError) else "error"
                    self.data.setdefault("code", "operation_timeout" if isinstance(exc, TimeoutError) else "operation_error")
                if self.data["outcome"] != "ok" and trace._failure is None:
                    trace._failure = self.data["name"]
        finally:
            if self.token is not None:
                trace._parent.reset(self.token)
            trace._overhead += time.perf_counter() - started
        return False  # Never swallow or replace a business exception.


class HelperTiming:
    """Bounded nested spans with a compact, JSON-serializable result summary.

    output_dir is a dedicated directory owned by this skill's timing collector.
    Only this collector's trace-<uuid>.json files are subject to retention.
    trace_ref in the result is relative to output_dir, not a Vida API field.
    max_spans bounds child records; the helper root is always retained.
    """

    def __init__(self, helper, *, output_dir=None, max_spans=256,
                 keep_runs=200, retention_seconds=7 * 24 * 60 * 60,
                 clock=time.monotonic):
        self.helper = _label(helper, "helper")
        self.trace_id = uuid.uuid4().hex
        self.root_id = uuid.uuid4().hex[:16]
        self.clock = clock
        self.started = clock()
        self.output_dir = Path(output_dir) if output_dir is not None else None
        self.max_spans = max(0, min(int(max_spans), 10_000))
        self.keep_runs = max(1, int(keep_runs))
        self.retention_seconds = max(1, int(retention_seconds))
        self._parent = ContextVar("helper_timing_parent", default=self.root_id)
        self._spans = []
        self._dropped = 0
        self._failure = None
        self._overhead = 0.0
        self._finished = False
        self._diagnostics = None

    def span(self, name, *, kind="step"):
        return _Span(self, name, kind)

    def finish(self, status="done", code=None):
        """Call after all work/spans close, on every normal or handled-error return.

        Freezes the work timeline before writing it. elapsed_ms includes final
        persistence; root/child spans end before persistence. instrumentation_ms
        measures collector work including persistence, and overlaps elapsed_ms.
        Repeated calls return the same diagnostics without writing again.
        """
        if self._finished:
            return dict(self._diagnostics)
        overhead_started = time.perf_counter()
        self._finished = True
        body_ms = _ms(self.clock() - self.started)
        outcome = {"done": "ok", "blocked": "blocked", "need_user": "need_user"}.get(status, "error")
        root = {"span_id": self.root_id, "parent_span_id": None, "name": self.helper,
                "kind": "helper", "start_ms": 0, "duration_ms": body_ms, "outcome": outcome}
        if code:
            root["code"] = _label(code, "helper_error")
        unfinished = 0
        for span in self._spans:
            if "duration_ms" not in span:
                span.update(duration_ms=max(0, body_ms - span["start_ms"]), outcome="unfinished")
                unfinished += 1
        phases = {}
        for span in self._spans:
            if span["parent_span_id"] == self.root_id and span["kind"] == "phase":
                phases[span["name"]] = phases.get(span["name"], 0) + span["duration_ms"]
        diagnostics = {"trace_id": self.trace_id, "phase_ms": phases,
                       "dropped_spans": self._dropped, "unfinished_spans": unfinished}
        if code:
            diagnostics["code"] = _label(code, "helper_error")
        if status != "done" or self._failure:
            diagnostics["phase"] = self._failure or (self._spans[-1]["name"] if self._spans else "helper")
        if self.output_dir is not None:
            payload = {"trace_id": self.trace_id, "helper": self.helper,
                       "body_elapsed_ms": body_ms, "inclusive_durations": True,
                       "dropped_spans": self._dropped, "unfinished_spans": unfinished,
                       "spans": [root, *self._spans]}
            try:
                diagnostics["trace_ref"] = self._write(payload)
            except Exception:
                diagnostics["trace_write_failed"] = True
        self._overhead += time.perf_counter() - overhead_started
        diagnostics.update(elapsed_ms=_ms(self.clock() - self.started),
                           instrumentation_ms=_ms(self._overhead))
        self._diagnostics = diagnostics
        return dict(diagnostics)

    def _write(self, payload):
        self.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        name = "trace-" + self.trace_id + ".json"
        path = self.output_dir / name
        # Exclusive creation prevents overwriting an existing output or symlink.
        with path.open("x", encoding="utf-8") as stream:
            path.chmod(0o600)
            json.dump(payload, stream, separators=(",", ":"))
        self._prune(path)
        return name

    def _prune(self, current):
        now = time.time()
        candidates = []
        for path in self.output_dir.iterdir():
            if _TRACE_FILE.fullmatch(path.name) and not path.is_symlink() and path.is_file():
                candidates.append((path.stat().st_mtime, path))
        candidates.sort(key=lambda item: (item[1] == current, item[0]), reverse=True)
        for index, (modified, path) in enumerate(candidates):
            if path != current and (index >= self.keep_runs or now - modified > self.retention_seconds):
                path.unlink()
