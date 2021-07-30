# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云 - 监控平台 (BlueKing - Monitor) available.
Copyright (C) 2017-2021 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""
#!/usr/bin/python
# -*- coding: utf-8 -*-


import cgi

from six.moves.BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

PORT_NUMBER = 8080


class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("Received")
        ctype, pdict = cgi.parse_header(self.headers.getheader("content-type"))
        if ctype == "multipart/form-data":
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == "application/x-www-form-urlencoded" or ctype == "application/json":
            length = int(self.headers.getheader("content-length"))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}
        print(ctype)
        print(postvars)
        return


if __name__ == "__main__":
    try:
        server = HTTPServer(("", PORT_NUMBER), MyHandler)
        print("Started http server on port ", PORT_NUMBER)
        server.serve_forever()
    except KeyboardInterrupt:
        print("^C received, shutting down the web server")
        server.socket.close()
