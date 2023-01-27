#  coding: utf-8
import socketserver

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

import os

class RequestHeaders():
    def __init__(self):
        self.type: str = None
        self.path: str = None
        self.version: str = None
        self.accept_encoding: str = None
        self.host: str = None
        self.user_agent: str = None
        self.connection: str = None
        self.content_type: str = None
        self.content_length: int = None
        self.data: str = None

class Response():
    def __init__(self):
        self.headers: dict = {}
        self.version: str = 'HTTP/1.1'
        self.status_code: int = 200
        self.status_text: str = 'OK'
        self.data: str = ''

BASE_PATH = './www'

class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip()
        if self.data == b'':
            return
        _request = self.break_up_request(self.data)
        response = None
        if _request.type == 'GET':
            response = self.on_get(_request)
        else:
            response = Response()
            response.status_code = 405
            response.status_text = 'Method Not Allowed'
        if not response:
            self.request.sendall(bytearray("OK",'utf-8'))
        response = self.build_response(response)
        self.request.sendall(response)

    def break_up_request(self,request:bytes) -> RequestHeaders:
        headers = request.split(b'\r\n')
        req_type = headers[0].split(b' ')
        headers = headers[1:]
        req_dict = {}
        next_data = False
        for header in headers:
            if next_data:
                temp = {b'Data': header}
                req_dict.update(temp)
                next_data = False
                continue
            hdr_split = header.split(b': ',1)
            if len(hdr_split) > 1:
                temp = {hdr_split[0]: hdr_split[1]}
                req_dict.update(temp)
            else:
                next_data = True
                continue
        request_headers = RequestHeaders()
        request_headers.type = req_type[0].decode('utf-8')
        request_headers.path = req_type[1].decode('utf-8')
        request_headers.version = req_type[2].decode('utf-8')
        if req_dict.get(b'Accept-Encoding'): request_headers.accept_encoding = req_dict.get(b'Accept-Encoding').decode('utf-8')
        if req_dict.get(b'Host'): request_headers.host = req_dict.get(b'Host').decode('utf-8')
        if req_dict.get(b'User-Agent'): request_headers.user_agent = req_dict.get(b'User-Agent').decode('utf-8')
        if req_dict.get(b'Connection'): request_headers.connection = req_dict.get(b'Connection').decode('utf-8')
        if req_dict.get(b'Content-Type'): request_headers.content_type = req_dict.get(b'Content-Type').decode('utf-8')
        if req_dict.get(b'Content-Length'): request_headers.content_length = int(req_dict.get(b'Content-Length').decode('utf-8'))
        if req_dict.get(b'Data'): request_headers.data = req_dict.get(b'Data').decode('utf-8')
        return request_headers

    def on_get(self,request:RequestHeaders) -> Response:
        response = Response()
        # folder given
        if os.path.isdir(BASE_PATH + request.path):
            if not request.path.endswith('/'):
                _path = request.path + '/'
                response.status_code = 301
                response.status_text = 'Moved'
                response.headers.update({'Content-Type': 'text/html'})
                response.headers.update({'Location': _path})
                return response
            file_to_serve = self.figure_directory(request.path)
            if file_to_serve:
                with open(file_to_serve, 'r') as f:
                    response.headers.update({'Content-Type': 'text/html'})
                    response.data = f.read()
            else:
                response.status_code = 404
                response.status_text = 'NOT FOUND'
        else:
            file_path = self.figure_path(request.path)
            if file_path:
                with open(file_path, 'r') as f:
                     response.data = f.read()
                if file_path.endswith('.css'):
                    response.headers.update({'Content-Type': 'text/css'})
                else:
                    response.headers.update({'Content-Type': 'text/html'})
            else:
                # file not found
                response.status_code = 404
                response.status_text = 'NOT FOUND'
        return response

    def on_put(self,request:RequestHeaders) -> Response:
        response = Response()
        return response

    def figure_directory(self,path):
        file = None
        if os.path.isdir(BASE_PATH + path):
            if os.path.isfile(BASE_PATH + path + 'index.html'):
                file = BASE_PATH + path + 'index.html'
        return file

    def figure_path(self,path) -> str:
        path = BASE_PATH + path
        if os.path.isfile(path):
            if os.path.commonprefix([os.path.abspath(path),os.path.abspath(BASE_PATH)]) == os.path.abspath(BASE_PATH):
                return path
        return None

    def build_response(self,response:Response):
        _data = bytes(b'')
        _headers = ''
        if not response.data == '':
            temp = {'Content-Length': len(response.data)}
            response.headers.update(temp)
            _data = b'\r\n' + b'\r\n' + response.data.encode('utf-8')
        for header in response.headers.items():
            _headers = _headers + str(header[0]) + ': ' + str(header[1]) + '\r\n'
        return response.version.encode('utf-8') + b' ' + str(response.status_code).encode('utf-8') + b' ' + response.status_text.encode('utf-8') + b'\r\n' + _headers.encode('utf-8') + _data

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
