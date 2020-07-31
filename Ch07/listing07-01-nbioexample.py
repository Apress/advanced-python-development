import select
import socket
import typing as t
import urllib.parse

import h11



def get_http(uri: str, headers: t.Dict[str, str]) -> socket.socket:
    """Given a URI and a set of headers, make a HTTP request and return the
    underlying socket. If there were a production-quality implementation of
    nonblocking HTTP this function would be replaced with the relevant one
    from that library."""
    parsed = urllib.parse.urlparse(uri)
    sock = socket.socket()
    if parsed.port:
        port = parsed.port
    else:
        port = 80
    headers["Host"] = parsed.netloc
    sock.connect((parsed.hostname, port))
    sock.setblocking(False)

    connection = h11.Connection(h11.CLIENT)
    request = h11.Request(method="GET", target=parsed.path, headers=headers.items())

    sock.send(connection.send(request))
    sock.send(connection.send(h11.EndOfMessage()))
    return sock


def read_from_socket(sock: socket.socket) -> str:
    """ If there were a production-quality implementation of nonblocking HTTP
    this function would be replaced with the relevant one to get the body of
    the response if it was a success or error otherwise. """
    data = sock.recv(1024000)
    connection = h11.Connection(h11.CLIENT)
    connection.receive_data(data)

    response = connection.next_event()
    headers = dict(response.headers)
    body = connection.next_event()
    eom = connection.next_event()

    try:
        if (
            response.status_code == 200
            and b"application/json" in headers.get(b"content-type", None) 
        ):
            return body.data.decode("utf-8")
        else:
            raise ValueError("Bad response")
    finally:
        sock.close()


def show_responses(uris: t.Tuple[str]) -> None:
    sockets = []
    for uri in uris:
        print(f"Making request to {uri}")
        sockets.append(get_http(uri, {}))
    while sockets:
        readable, writable, exceptional = select.select(sockets, [], [])
        print(f"{ len(readable) } socket(s) ready")
        for request in readable:
            print(f"Reading from socket")
            response = read_from_socket(request)
            print(f"Got { len(response) } bytes")
            sockets.remove(request)



if __name__ == "__main__":
    show_responses([
        "http://jsonplaceholder.typicode.com/posts?userId=1",
        "http://jsonplaceholder.typicode.com/posts?userId=5",
        "http://jsonplaceholder.typicode.com/posts?userId=8",
    ])
