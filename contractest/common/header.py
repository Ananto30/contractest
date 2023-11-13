from dataclasses import dataclass
from typing import List, Union

from requests.structures import CaseInsensitiveDict

from contractest.common.discrepancy import Discrepancy, DiscrepancyTypes
from contractest.config import config

cookies_headers = [
    "set-cookie",
    "cookie",
]


@dataclass
class Headers:
    val: dict

    @classmethod
    def from_dict(cls, headers: Union[CaseInsensitiveDict, dict]):
        return cls({k.lower(): v for k, v in headers.items()})

    def to_dict(self):
        return self.val

    def has(self, header: str) -> bool:
        return header in self.val

    def get(self, header: str) -> str:
        return self.val.get(header, "")

    def set(self, header: str, value: str):
        self.val[header] = value

    def cookies(self) -> dict:
        cookies = {}
        for cookie_header in cookies_headers:
            if cookie_header in self.val:
                cookies.update(self._parse_cookie(self.val[cookie_header]))

        for ic in config.headers_comparison.ignore_cookies:
            if ic in cookies:
                cookies.pop(ic)
        return cookies

    def _parse_cookie(self, cookie_header: str) -> dict:
        cookies = {}
        for cookie in cookie_header.split(";"):
            if "=" not in cookie:
                continue
            key, value = cookie.split("=", 1)
            cookies[key.strip()] = value.strip()
        return cookies

    def set_cookie(self, cookie: str, value: str):
        cookies = self.cookies()
        cookies[cookie] = value
        for cookie_header in cookies_headers:
            if cookie_header in self.val:
                self.val[cookie_header] = self._cookies_dict_to_str(cookies)

    def _cookies_dict_to_str(self, cookies: dict) -> str:
        return "; ".join([f"{k}={v}" for k, v in cookies.items()])

    def headers_without_cookies(self) -> dict:
        headers = self.val.copy()
        for cookie_header in cookies_headers:
            if cookie_header in headers:
                headers.pop(cookie_header)

        for ih in config.headers_comparison.ignore_headers:
            if ih in headers:
                headers.pop(ih)
        return headers

    def compare(self, expected_headers: "Headers") -> List[Discrepancy]:
        discrepancies = []

        self_cookies = self.cookies()
        expected_cookies = expected_headers.cookies()
        for self_cookie, exp_cookie in zip(self_cookies, expected_cookies):
            if self_cookie != exp_cookie:
                discrepancies.append(
                    Discrepancy(
                        f"Cookie {self_cookie} is not equal to {exp_cookie}",
                        DiscrepancyTypes.VALUE_MISMATCH,
                        "header",
                        exp_cookie,
                        self_cookie,
                    )
                )

        self_headers = self.headers_without_cookies()
        exp_headers = expected_headers.headers_without_cookies()
        for self_header, expected_header in zip(self_headers, exp_headers):
            if self_header != expected_header:
                discrepancies.append(
                    Discrepancy(
                        f"Header {self_header} is not equal to {expected_header}",
                        DiscrepancyTypes.VALUE_MISMATCH,
                        "header",
                        expected_header,
                        self_header,
                    )
                )

        return discrepancies
