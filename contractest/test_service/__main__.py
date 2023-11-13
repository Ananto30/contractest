from contractest.common.store import ContractStore
from contractest.config import config
from contractest.test_service.server import ContractServerTester

if __name__ == "__main__":
    contract_store = ContractStore()
    contract_store.load(config.test_service.load_from_folder)

    if not contract_store.get_all():
        print("No contracts found, exiting")
        exit(1)

    contract_server_tester = ContractServerTester(
        config.test_service.server_base_url,
        contract_store,
    )
    contract_server_tester.test()
