"""
Author: Oleg Shkolnik יא9.
Description: Server that receive GET request from client (site) and send answer:
             status of request (200 OK / 404 Not Found / 400 Bad Request / 302 Moved Temporarily / 403 Forbidden / 500 Internal Server Error),
             length of content,
             type of content,
             content.
Date: 11/01/24
"""


import socket
import os
from protocol import *


HOST = '0.0.0.0'
PORT = 80
SITE_FOLDER = 'webroot'
MOVED_URL = '/index.html'
SOCKET_TIMEOUT = 2
specific_urls = ['forbidden', 'moved', 'error']
request_error = b"HTTP/1.1 400 Bad Request\r\n\r\n<h1>400 Bad Request</h1>"
types = {
    'tml': 'text/html;charset=utf-8',
    'css': 'text/css',
    '.js': 'text/javascript; charset=UTF-8',
    'txt': 'text/plain',
    'ico': 'image/x-icon',
    'gif': 'image/jpeg',
    'jpg': 'image/jpeg',
    'png': 'image/jpeg'
}


def choosing_type(filename):
    """
    function for searching type of file
    :param filename: file which type we want to know
    :return: type
    """
    content_type = types[filename[-3:]]
    return content_type


def specific(filename):
    """
    function checks if we have specific url
    :param filename: specific part
    :return: true or false
    """
    return filename in specific_urls


def searching_url(filename):
    """
    function that determines what response we need to send on specific url
    :param filename: specific url
    :return: specific response
    """
    response = b''
    if filename == 'forbidden':
        response = b"HTTP/1.1 403 Forbidden\r\n\r\n<h1>403 Forbidden</h1>"
    elif filename == 'moved':
        response = b"HTTP/1.1 302 Moved Temporarily\r\nLocation: " + bytes(MOVED_URL, 'utf-8') + b"\r\n\r\n"
    elif filename == 'error':
        response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n<h1>500 Internal Server Error</h1>"
    return response


def validating_error(request):
    """
    function validates if GET request is correct
    :param request: GET request in type of list
    :return: true if request is correct and false if not
    """

    return request[0] == "GET" and request[2] == "HTTP/1.1"


def receive_all(sock, def_size=1024):
    """
    function make sure that we received all information
    :param sock: socket of client from which we receiv data
    :param def_size: default type of socket.recv
    :return: all data
    """
    data = b''
    while True:
        chunk = sock.recv(def_size)
        if not chunk:
            break
        data += chunk
        if len(chunk) < def_size:
            break
    return data


def serve_file(client_socket, filename):
    """
    This function opens a file requested from the browser and sends its contents to the client via a socket.
    If the file is not found, a "404 Not Found" message is sent.
    :param client_socket: socket of client
    :param filename: path to the file
    """
    try:
        with open(filename, 'rb') as file:
            content = file.read()
            content_type = choosing_type(filename)
            headers = f"Content-Type: {content_type}\nContent-Length: {len(content)}\r\n\r\n".encode()
            response = b"HTTP/1.1 200 OK\r\n" + headers + content
            client_socket.sendall(response)
    except FileNotFoundError:
        with open(r'webroot\imgs\error.jpg', 'rb') as file:
            content = file.read()
            headers = f"Content-Type: {types['jpg']}\nContent-Length: {len(content)}\r\n\r\n".encode()
            response = b"HTTP/1.1 404 Not Found\r\n" + headers + content
        client_socket.sendall(response)


def main():
    """
    This function creates a server socket that accepts requests from clients.
    When a request is received, a new socket is opened for the client.
    The server then accepts the request from the client, processes it,
    and sends a response back to the client via the created socket.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"the server is running on the port {PORT}")

        while True:
            """
            Requests from the client are processed.
            The requested file is extracted from the request and 
            the path to this file is formed in accordance with the site folder.
            If the request contains an error or the file path is not specified,
            the server sends back a "400 Bad Request" message.
            """
            client_socket, addr = server_socket.accept()
            try:
                client_socket.settimeout(SOCKET_TIMEOUT)
                print(f"Connection established with {addr}")

                request = receive_all(client_socket).decode()
                if request:
                    request_split = request.split()
                    print(request_split)
                    if validating_error(request_split):
                        if len(request_split) > 1:
                            filename = request_split[1][1:]
                            if filename == '':
                                filename = 'index.html'

                            filepath = os.path.join(SITE_FOLDER, filename)

                            if "../" not in filename:
                                """
                                Specific URLs are checked.
                                
                                If the request contains the URL /forbidden, the server sends a "403 Forbidden" error.
                                
                                If the request comes to the /error URL, 
                                the server sends a "500 Internal Server Error" error.
                                
                                If the request comes to the /moved URL, 
                                the server sends "302 Moved Temporarily" as well as the site location.
                                
                                Otherwise, the server serves the requested file or sends a "400 Bad Request"
                                if the request contains an error.
                                """

                                if specific(filename):
                                    response = searching_url(filename)
                                    client_socket.sendall(response)
                                else:
                                    serve_file(client_socket, filepath)
                            else:
                                response = request_error
                                client_socket.sendall(response)
                else:
                    response = request_error
                    client_socket.sendall(response)

            except socket.error as err:
                """
                Send the name of error in error situation
                """
                print('received socket error on server socket' + str(err))

            finally:
                """
                Close the socket anyway
                """
                client_socket.close()

    except socket.error as err:
        """
        Send the name of error in error situation
        """
        print('received socket error on server socket' + str(err))

    finally:
        """
        Close the socket anyway
        """
        server_socket.close()


if __name__ == "__main__":
    """
       checking function situations and launching the main
    """
    assert specific('error')
    assert specific('forbidden')
    assert specific('moved')
    assert not specific('abc')
    assert searching_url('error')
    assert not searching_url('abc')
    assert choosing_type('jpg')
    assert validating_error(['GET', '/', 'HTTP/1.1', 'headers'])
    assert not validating_error(['POST', '/', 'HTTP/1.1', 'headers'])
    main()
