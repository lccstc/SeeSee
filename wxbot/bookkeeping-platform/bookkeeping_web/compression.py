from __future__ import annotations

import gzip
from collections.abc import Iterator, Sequence

_COMPRESSIBLE_TYPES = (
    "text/",
    "application/json",
    "application/javascript",
    "application/xml",
    "image/svg+xml",
)


def gzip_middleware(
    app,
    *,
    minimum_size: int = 1024,
    maximum_size: int = 512 * 1024,
    compresslevel: int = 5,
):
    def wrapped_app(environ, start_response):
        request_method = str(environ.get("REQUEST_METHOD") or "GET").upper()
        accept_encoding = str(environ.get("HTTP_ACCEPT_ENCODING") or "")
        wants_gzip = _client_accepts_gzip(accept_encoding)

        captured: dict[str, object] = {}
        buffered_events: list[bytes] = []

        def capture_start_response(status, headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = list(headers)
            captured["exc_info"] = exc_info

            def write(data: bytes) -> None:
                buffered_events.append(bytes(data))

            return write

        result = app(environ, capture_start_response)
        status = str(captured.get("status") or "200 OK")
        headers = list(captured.get("headers") or [])
        exc_info = captured.get("exc_info")

        if not wants_gzip:
            start_response(status, headers, exc_info)
            return _passthrough_response(result, buffered_events, head_only=request_method == "HEAD")

        header_map = {key.lower(): value for key, value in headers}
        content_type = str(header_map.get("content-type") or "").lower()
        media_type = content_type.split(";", 1)[0].strip()
        content_length = _parse_content_length(header_map.get("content-length"))
        cache_control = str(header_map.get("cache-control") or "").lower()
        should_compress = (
            status.startswith("200")
            and content_length is not None
            and minimum_size <= content_length <= maximum_size
            and "no-transform" not in cache_control
            and "content-encoding" not in header_map
            and media_type != "text/event-stream"
            and any(media_type.startswith(prefix) for prefix in _COMPRESSIBLE_TYPES)
            and isinstance(result, (list, tuple))
        )
        if not should_compress:
            start_response(status, headers, exc_info)
            return _passthrough_response(result, buffered_events, head_only=request_method == "HEAD")

        try:
            body_parts = list(buffered_events)
            body_parts.extend(bytes(chunk) for chunk in result)
            body = b"".join(body_parts)
        finally:
            _close_result(result)

        compressed = gzip.compress(body, compresslevel=compresslevel)
        filtered_headers = [
            (key, value)
            for key, value in headers
            if key.lower() not in {"content-length", "content-encoding", "vary", "etag"}
        ]
        filtered_headers.append(("Content-Encoding", "gzip"))
        filtered_headers.append(("Vary", _merge_vary_headers(headers)))
        filtered_headers.append(("Content-Length", str(len(compressed))))
        start_response(status, filtered_headers, exc_info)
        if request_method == "HEAD":
            return []
        return [compressed]

    close = getattr(app, "close", None)
    if callable(close):
        wrapped_app.close = close  # type: ignore[attr-defined]
    return wrapped_app


def _passthrough_response(result, buffered_events: list[bytes], *, head_only: bool):
    if head_only:
        _close_result(result)
        return []

    def generate() -> Iterator[bytes]:
        iterator = iter(result)
        emitted = 0
        try:
            while True:
                while emitted < len(buffered_events):
                    yield buffered_events[emitted]
                    emitted += 1
                try:
                    chunk = next(iterator)
                except StopIteration:
                    break
                while emitted < len(buffered_events):
                    yield buffered_events[emitted]
                    emitted += 1
                yield bytes(chunk)
            while emitted < len(buffered_events):
                yield buffered_events[emitted]
                emitted += 1
        finally:
            _close_result(result)

    return generate()


def _close_result(result) -> None:
    close = getattr(result, "close", None)
    if callable(close):
        close()


def _client_accepts_gzip(accept_encoding: str) -> bool:
    gzip_quality: float | None = None
    wildcard_quality: float | None = None
    for part in str(accept_encoding or "").split(","):
        token = part.strip()
        if not token:
            continue
        name, _, params = token.partition(";")
        encoding = name.strip().lower()
        if encoding not in {"gzip", "*"}:
            continue
        quality = 1.0
        for item in params.split(";"):
            field = item.strip()
            if not field or not field.lower().startswith("q="):
                continue
            try:
                quality = float(field.split("=", 1)[1].strip())
            except ValueError:
                quality = 0.0
        if encoding == "gzip":
            gzip_quality = quality
        else:
            wildcard_quality = quality
    if gzip_quality is not None:
        return gzip_quality > 0
    if wildcard_quality is not None:
        return wildcard_quality > 0
    return False


def _parse_content_length(value: str | None) -> int | None:
    try:
        parsed = int(str(value or "").strip())
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _merge_vary_headers(headers: Sequence[tuple[str, str]]) -> str:
    values: list[str] = []
    seen_lower: set[str] = set()
    for key, value in headers:
        if key.lower() != "vary":
            continue
        for item in str(value or "").split(","):
            text = item.strip()
            lowered = text.lower()
            if text and lowered not in seen_lower:
                values.append(text)
                seen_lower.add(lowered)
    if "accept-encoding" not in seen_lower:
        values.append("Accept-Encoding")
    return ", ".join(values)
