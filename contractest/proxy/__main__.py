from contractest.config import config
from contractest.proxy.proxy import APIProxy, contract_store

if __name__ == "__main__":
    try:
        proxy = APIProxy(
            proxy_host=config.proxy.host,
            proxy_port=config.proxy.port,
        )
        proxy.run()
    except KeyboardInterrupt:
        contract_store.write(path=config.proxy.save_to_folder)
        print(f"Contracts written to {config.proxy.save_to_folder}")
