import logging
from typing import Any, Dict

import requests
from termcolor import cprint

from contractest.common.body import Body
from contractest.common.contract import Contract, ContractFlow
from contractest.common.header import Headers
from contractest.common.store import ContractStore

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

simple_store: Dict[str, Any] = {}


class ContractServerTester:
    def __init__(self, base_url: str, contract_store: ContractStore) -> None:
        self.base_url = base_url
        self.contract_store = contract_store

    def test(self):
        for flow in self.contract_store.flow:
            contract = self.contract_store.get(flow.contract_hash)
            self._test_contract(flow, contract)

    def _test_contract(self, flow: ContractFlow, contract: Contract):
        print("=" * 80)
        cprint(
            f"Testing: {contract.method.upper()} {contract.path}",
            attrs=["bold"],
        )

        # modify contract with values from store
        for flow_use in flow.use:
            flow_use.set_param_value_in_contract(contract, simple_store[flow_use.key])

        log.debug("Request: %s", contract.request_body.dict)

        response = requests.request(
            contract.method,
            f"{self.base_url}{contract.path}",
            headers=contract.request_headers.to_dict(),
            json=contract.request_body.body,
            timeout=10,
        )

        if response.status_code != contract.response_status_code:
            cprint(
                "Failed, status code mismatch \n"
                f"Expected status code: {contract.response_status_code} \n"
                f"Got: {response.status_code} \n"
                f"Got response body: {response.text}",
                color="red",
            )
            return

        response_headers = Headers.from_dict(response.headers)
        response_body = Body(response.text, contract.path)

        log.debug("Response: %s", response_body.dict)

        # store values from response
        for flow_store in flow.store:
            simple_store[flow_store.key] = flow_store.parse_param_value_from_response(
                response
            )

        contract_headers = contract.response_headers
        header_discrepancies = response_headers.compare(contract_headers)
        for d in header_discrepancies:
            cprint(
                "Failed, headers mismatch \n" f"{d}",
                color="red",
            )

        contract_body = contract.response_body
        body_discrepancies = response_body.compare(contract_body)
        for d in body_discrepancies:
            cprint(
                "Failed, body mismatch \n" f"{d}",
                color="red",
            )

        if body_discrepancies:
            # print(print_dict_str(response_body.dict, body_discrepancies))
            # pprint(response_body.dict)
            return

        cprint("Passed!", color="green")
