import time
import wsgiref.simple_server


def hello_world(environ, start_response):
    headers = [
        ("Content-type", "text/html; charset=utf-8"),
        ("Content-Security-Policy", "default-src 'none';"),
    ]
    start_response("200 OK", headers)
    yield b"<html><body>"
    for i in range(20):
        yield b"<p>hello world</p>"
        time.sleep(1)
    yield b"</body></html>"

if __name__ == "__main__":
    with wsgiref.simple_server.make_server("", 8000, hello_world) as server:
        server.serve_forever()
