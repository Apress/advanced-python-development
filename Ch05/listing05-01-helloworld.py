import wsgiref.simple_server

def hello_world(environ, start_response):
    headers = [
        ("Content-type", "text/plain; charset=utf-8"),
        ("Content-Security-Policy", "default-src 'none';"),
    ]
    start_response("200 OK", headers)
    return [b"hello", b" ", b"world"]

if __name__ == "__main__":
    with wsgiref.simple_server.make_server("", 8000, hello_world) as server:
        server.serve_forever()
