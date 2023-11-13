import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from termcolor import cprint

from contractest.common.body import Body
from contractest.common.contract import Contract
from contractest.common.header import Headers
from contractest.common.store import ContractStore
from contractest.config import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


contract_store = ContractStore()


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        self.base_url = config.proxy.server_base_url

        super().__init__(*args, **kwargs)

    def do_GET(self):
        self._handle_request("get", requests.get)

    def do_DELETE(self):
        self._handle_request("delete", requests.delete)

    def do_POST(self):
        self._handle_request("post", requests.post)

    def do_PUT(self):
        self._handle_request("put", requests.put)

    def do_PATCH(self):
        self._handle_request("patch", requests.patch)

    def _handle_request(self, method, requests_func):
        req_path = self.path
        req_headers = Headers.from_dict(self.headers)
        req_body = self.rfile.read(
            int(req_headers.get("content-length"))
            if req_headers.has("content-length")
            else 0
        )
        url = f"{self.base_url}{req_path}"

        log.debug(f"Proxying {method.upper()} {url}")
        resp = requests_func(
            url,
            data=req_body,
            headers=req_headers.to_dict(),
            verify=True,
        )

        resp_headers = Headers.from_dict(resp.headers)
        resp_headers_dict = resp_headers.to_dict()
        resp_body = resp.content
        resp_status_code = resp.status_code

        contract = Contract(
            path=req_path,
            method=method,
            request_headers=req_headers,
            request_body=Body(req_body.decode("utf-8"), req_path),
            response_headers=resp_headers,
            response_body=Body(resp_body.decode("utf-8"), req_path),
            response_status_code=resp_status_code,
        )
        contract_store.add(contract)
        cprint(f"Contract added: {method.upper()} {req_path}", color="green")

        self.send_response(resp_status_code)
        for key in resp_headers_dict:
            self.send_header(key, resp_headers_dict[key])
        self.end_headers()
        self.wfile.write(resp_body)
        self.wfile.flush()


class APIProxy:
    def __init__(
        self,
        proxy_host="127.0.0.1",
        proxy_port=6000,
    ) -> None:
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def run(self) -> None:
        server_address = (self.proxy_host, self.proxy_port)
        httpd = HTTPServer(server_address, ProxyHandler)
        print(f"Starting proxy server on {self.proxy_host}:{self.proxy_port}")
        print(f"Proxying to {config.proxy.server_base_url}")
        httpd.serve_forever()
