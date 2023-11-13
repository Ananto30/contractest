from dataclasses import dataclass
from typing import Dict, List, Optional

import toml


@dataclass
class ProxyConfig:
    host: str = "localhost"
    port: int = 8000
    server_base_url: str = "http://localhost:7777"
    save_to_folder: str = "./contracts"


@dataclass
class TestServiceConfig:
    load_from_folder: str = "./contracts"
    server_base_url: str = "http://localhost:7777"


@dataclass
class BodyComparisonConfig:
    strict_match: bool = False
    value_match: bool = True
    structure_match: bool = True
    array_length_match: bool = True
    array_order_match: bool = True
    ignore_fields: Optional[List[str]] = None
    ignore_fields_by_path: Optional[Dict[str, List[str]]] = None


@dataclass
class HeaderComparisonConfig:
    ignore_headers: Optional[List[str]] = None
    ignore_cookies: Optional[List[str]] = None


@dataclass
class Config:
    proxy: ProxyConfig
    test_service: TestServiceConfig
    body_comparison: BodyComparisonConfig
    headers_comparison: HeaderComparisonConfig


def load_config(config_file):
    """
    Load configurations from a file.
    """
    with open(config_file) as f:
        config = toml.load(f)

    proxy_config = ProxyConfig(**config["proxy"])
    test_service_config = TestServiceConfig(**config["test_service"])
    body_comparison_config = BodyComparisonConfig(**config["body_comparison"])
    header_comparison_config = HeaderComparisonConfig(**config["headers_comparison"])

    return Config(
        proxy=proxy_config,
        test_service=test_service_config,
        body_comparison=body_comparison_config,
        headers_comparison=header_comparison_config,
    )


config = load_config("conf.toml")
