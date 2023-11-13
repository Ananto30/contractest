import hashlib
import json
from dataclasses import dataclass
from typing import Any, List

import requests

from contractest.common.body import Body
from contractest.common.header import Headers


@dataclass
class Contract:
    path: str
    method: str

    request_headers: Headers
    request_body: Body
    response_headers: Headers
    response_body: Body
    response_status_code: int

    def hash(self) -> str:
        return hashlib.md5(
            json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "method": self.method,
            "request_headers": self.request_headers.to_dict(),
            "request_body": self.request_body.dict,
            "response_headers": self.response_headers.to_dict(),
            "response_body": self.response_body.dict,
            "response_status_code": self.response_status_code,
        }


class ParameterPosition:
    HEADER = "header"
    BODY = "body"
    PATH = "path"
    QUERY = "query"
    COOKIES = "cookies"


@dataclass
class ContractFlowStoreModel:
    key: str
    parameter_position: ParameterPosition
    parameter_name: str  # can be json path for nested objects

    _value: Any = None

    def parse_param_value_from_contract(self, contract: Contract) -> Any:
        if self.parameter_position == ParameterPosition.BODY:
            return self._parse_json_path(
                contract.response_body.dict, self.parameter_name
            )
        elif self.parameter_position == ParameterPosition.HEADER:
            return contract.response_headers.get(self.parameter_name)
        elif self.parameter_position == ParameterPosition.COOKIES:
            return contract.response_headers.cookies().get(self.parameter_name)
        else:
            raise ValueError(
                f"Invalid parameter_position {self.parameter_position}, "
                "only header, cookies and body are supported in 'store'"
            )

    def parse_param_value_from_response(self, response: requests.Response) -> Any:
        if self.parameter_position == ParameterPosition.BODY:
            return self._parse_json_path(response.json(), self.parameter_name)
        elif self.parameter_position == ParameterPosition.HEADER:
            return response.headers.get(self.parameter_name)
        elif self.parameter_position == ParameterPosition.COOKIES:
            return response.cookies.get(self.parameter_name)
        else:
            raise ValueError(
                f"Invalid parameter_position {self.parameter_position}, "
                "only header, cookies and body are supported in 'store'"
            )

    def _parse_json_path(self, data: dict, path: str) -> Any:
        for key in path.split("."):
            if key.isdigit():
                data = data[int(key)]
            else:
                data = data[key]
        return data

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "parameter_position": self.parameter_position,
            "parameter_name": self.parameter_name,
        }


@dataclass
class ContractFlowUseValue:
    key: str
    parameter_position: ParameterPosition
    parameter_name: str  # can be json path for nested objects

    def set_param_value_in_contract(self, contract: Contract, value: Any):
        if self.parameter_position == ParameterPosition.BODY:
            data = contract.request_body.dict
            self._set_json_path(data, self.parameter_name, value)
            contract.request_body = Body(json.dumps(data), contract.path)
        elif self.parameter_position == ParameterPosition.HEADER:
            contract.request_headers.set(self.parameter_name, str(value))
        elif self.parameter_position == ParameterPosition.COOKIES:
            contract.request_headers.set_cookie(self.parameter_name, str(value))
        elif self.parameter_position == ParameterPosition.PATH:
            contract.path = contract.path.replace(self.parameter_name, str(value))
        elif self.parameter_position == ParameterPosition.QUERY:
            url = contract.path.split("?")
            query = url[1].split("&")
            for i, q in enumerate(query):
                if q.startswith(self.parameter_name):
                    query[i] = f"{self.parameter_name}={value}"
            contract.path = f"{url[0]}?{'&'.join(query)}"
        else:
            raise ValueError(
                "Invalid parameter_position, only header and body are supported in 'use'"
            )

    def _set_json_path(self, data: dict, path: str, value: Any):
        for key in path.split(".")[:-1]:
            data = data[key]
        data[path.split(".")[-1]] = value

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "parameter_position": self.parameter_position,
            "parameter_name": self.parameter_name,
        }


@dataclass
class ContractFlow:
    path: str
    method: str
    store: List[ContractFlowStoreModel]
    use: List[ContractFlowUseValue]
    contract_hash: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "method": self.method,
            "store": [s.to_dict() for s in self.store],
            "use": [u.to_dict() for u in self.use],
            "contract_hash": self.contract_hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContractFlow":
        return cls(
            path=data["path"],
            method=data["method"],
            store=[
                ContractFlowStoreModel(
                    key=s["key"],
                    parameter_position=s["parameter_position"],
                    parameter_name=s["parameter_name"],
                )
                for s in data["store"]
            ],
            use=[
                ContractFlowUseValue(
                    key=u["key"],
                    parameter_position=u["parameter_position"],
                    parameter_name=u["parameter_name"],
                )
                for u in data["use"]
            ],
            contract_hash=data["contract_hash"],
        )
