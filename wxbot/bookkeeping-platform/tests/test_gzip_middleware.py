from __future__ import annotations

import gzip
import unittest


class GzipMiddlewareTests(unittest.TestCase):
    def test_compresses_large_html_when_client_accepts_gzip(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("A" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip, deflate",
                },
                start_response,
            )
        )
        headers = captured["headers"]
        self.assertEqual(captured["status"], "200 OK")
        self.assertEqual(headers["Content-Encoding"], "gzip")
        self.assertEqual(headers["Vary"], "Accept-Encoding")
        self.assertEqual(int(headers["Content-Length"]), len(result))
        self.assertEqual(gzip.decompress(result), body)

    def test_preserves_existing_vary_headers_when_compressing(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("{" + ("x" * 2048) + "}").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("Vary", "Origin"),
                    ("Vary", "Accept"),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = headers

        _ = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        vary_values = [value for key, value in captured["headers"] if key == "Vary"]
        self.assertEqual(vary_values, ["Origin, Accept, Accept-Encoding"])

    def test_respects_gzip_q_zero(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("A" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "br, gzip;q=0",
                },
                start_response,
            )
        )
        self.assertNotIn("Content-Encoding", captured["headers"])
        self.assertEqual(result, body)

    def test_explicit_gzip_q_zero_overrides_wildcard(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("B" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip;q=0, *;q=1",
                },
                start_response,
            )
        )
        self.assertNotIn("Content-Encoding", captured["headers"])
        self.assertEqual(result, body)

    def test_supports_wsgi_write_callable(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("A" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            writer = start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            writer(body)
            return []

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

            def write(_data: bytes) -> None:
                raise AssertionError("outer start_response write should not be used")

            return write

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertEqual(captured["headers"]["Content-Encoding"], "gzip")
        self.assertEqual(gzip.decompress(result), body)

    def test_preserves_write_order_during_iteration(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        def app(environ, start_response):
            writer = start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(6000)),
                ],
            )

            def generate():
                yield b"A" * 2000
                writer(b"B" * 2000)
                yield b"C" * 2000

            return generate()

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

            def write(_data: bytes) -> None:
                raise AssertionError("outer start_response write should not be used")

            return write

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertNotIn("Content-Encoding", captured["headers"])
        self.assertEqual(result, b"A" * 2000 + b"B" * 2000 + b"C" * 2000)

    def test_skips_event_stream_responses(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = (b"data: ping\n\n" * 200)

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/event-stream; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertNotIn("Content-Encoding", captured["headers"])
        self.assertEqual(result, body)

    def test_drops_etag_when_response_is_gzipped(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("C" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("ETag", '"abc123"'),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertEqual(captured["headers"]["Content-Encoding"], "gzip")
        self.assertNotIn("ETag", captured["headers"])
        self.assertEqual(gzip.decompress(result), body)

    def test_head_request_keeps_gzip_metadata_without_body(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("E" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "HEAD",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertEqual(result, b"")
        self.assertEqual(captured["headers"]["Content-Encoding"], "gzip")
        self.assertEqual(captured["headers"]["Vary"], "Accept-Encoding")
        self.assertLess(int(captured["headers"]["Content-Length"]), len(body))

    def test_respects_cache_control_no_transform(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = ("<html>" + ("D" * 4096) + "</html>").encode("utf-8")

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "text/html; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                    ("Cache-Control", "public, no-transform"),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["headers"] = dict(headers)

        result = b"".join(
            wrapped(
                {
                    "REQUEST_METHOD": "GET",
                    "HTTP_ACCEPT_ENCODING": "gzip",
                },
                start_response,
            )
        )
        self.assertNotIn("Content-Encoding", captured["headers"])
        self.assertEqual(result, body)

    def test_skips_compression_when_client_does_not_accept_gzip(self) -> None:
        from bookkeeping_web.compression import gzip_middleware

        body = b'{"ok": true}'

        def app(environ, start_response):
            start_response(
                "200 OK",
                [
                    ("Content-Type", "application/json; charset=utf-8"),
                    ("Content-Length", str(len(body))),
                ],
            )
            return [body]

        wrapped = gzip_middleware(app)
        captured: dict[str, object] = {}

        def start_response(status, headers, exc_info=None):
            captured["status"] = status
            captured["headers"] = dict(headers)

        result = b"".join(wrapped({"REQUEST_METHOD": "GET"}, start_response))
        headers = captured["headers"]
        self.assertEqual(captured["status"], "200 OK")
        self.assertNotIn("Content-Encoding", headers)
        self.assertEqual(result, body)


if __name__ == "__main__":
    unittest.main()
