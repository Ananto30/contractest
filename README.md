# Contractest

Generate contract and test that against a service.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Generate contract

- Use the proxy in between service A and B. So if we want to test B, change the port of B to `7777` (default, can be configured in [`conf.toml`](conf.toml)). Adjust the proxy port so that A can talk to proxy and proxy talks to B and run the proxy:

    ```bash
    python -m contractest.proxy
    ```

- Now send request from A. If A is a frontend/webapp just browse. You can also make flows like going through pages, clicking buttons, etc.

- Notice the proxy is recording the contracts.

- Quit (Ctrl+C) the proxy and the contracts are saved in [`contracts`](contracts). (Can be configured in [`conf.toml`](conf.toml))

There is already a sample contract in the repo. You can use that to test the service.

## Test service

- Run the service. In this example, B. Configure the service url in [`conf.yaml`](conf.yaml).

- Run the test:

    ```bash
    python -m contractest.test_service
    ```