import json
from typing import Dict, List

import yaml

from contractest.common.body import Body
from contractest.common.contract import Contract, ContractFlow
from contractest.common.header import Headers


class ContractStore:
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.flow: List[ContractFlow] = []

    def add(self, contract: Contract):
        self.contracts[contract.hash()] = contract
        self.flow.append(
            ContractFlow(
                path=contract.path,
                method=contract.method,
                store=[],
                use=[],
                contract_hash=contract.hash(),
            )
        )

    def get(self, contract_hash: str) -> Contract:
        return self.contracts[contract_hash]

    def get_all(self) -> List[Contract]:
        return list(self.contracts.values())

    def write(self, path: str = "contracts"):
        flow_file = path + "/flow.yaml"
        contracts_file = path + "/contracts.json"

        with open(flow_file, "w") as f:
            f.write(yaml.dump(f.to_dict() for f in self.flow))

        with open(contracts_file, "w") as f:
            f.write(
                json.dumps(
                    {k: v.to_dict() for k, v in self.contracts.items()},
                )
            )

    def load(self, path: str = "contracts"):
        flow_file = path + "/flow.yaml"
        contracts_file = path + "/contracts.json"

        with open(contracts_file, "r") as f:
            contracts = json.loads(f.read())

        for hash, contract in contracts.items():
            c = Contract(
                path=contract["path"],
                method=contract["method"],
                request_headers=Headers.from_dict(contract["request_headers"]),
                request_body=Body(
                    contract["request_body"],
                    contract["path"],
                ),
                response_headers=Headers.from_dict(contract["response_headers"]),
                response_body=Body(
                    contract["response_body"],
                    contract["path"],
                ),
                response_status_code=contract["response_status_code"],
            )
            self.add(c)
            print(f"Loaded contract: {c.method.upper()} {c.path} : {c.hash()}")

        with open(flow_file, "r") as f:
            flow = yaml.load(f.read(), Loader=yaml.FullLoader)

        # replace the flow with the loaded flow
        self.flow = [ContractFlow.from_dict(f) for f in flow]
