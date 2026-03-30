[![PyPI](https://img.shields.io/pypi/v/natsrpy?style=for-the-badge)](https://pypi.org/project/natsrpy/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/natsrpy?style=for-the-badge)](https://pypistats.org/packages/natsrpy)

# Nats client

This is a client library for [NATS](https://nats.io) written in rust.

## Sponsors of this project

Special thanks for supporting development of this project.

<div align="center">
    <a href="https://intree.com">
        <picture align="center">
          <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/07a81bdc-639d-44d9-afa2-49203bfb38a9">
          <source media="(prefers-color-scheme: light)" srcset="https://github.com/user-attachments/assets/a2b0e9bc-cebb-4565-af0a-780e79ef2ce5">
         <img alt="Fallback image description" width="400">
        </picture>
    </a>
    <p>share to connect</p>
</div>

## installation

This package can be installed from pypi:

```bash
pip install natsrpy
```

Or alternatively you can build it yourself using maturin, and stable rust.

## Usage

```python
import asyncio

from natsrpy import Nats

async def main() -> None:
    nats = Nats(["nats://localhost:4222"])
    await nats.startup()

    subscription = await nats.subscribe("hello")

    await nats.publish("hello", "str world")

    subscription.unsubscribe(limit=1)
    async for message in subscription:
        print(message)

    # Don't forget to call shutdown.
    await nats.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

You can see more usage examples in our [examples](https://github.com/taskiq-python/natsrpy/tree/master/examples) folder.

Also, our [tests](https://github.com/taskiq-python/natsrpy/tree/master/python/tests)
are written in python and could be a good place to discover features and the way they intended to be used.

As of for now, our documentation is only availabe in source code. You can see it in our [type-stubs folder](https://github.com/taskiq-python/natsrpy/tree/master/python/natsrpy/_natsrpy_rs).

## Development

We use stable rust and pyo3 for writing python extension module.
In order to build the project, use uv and maturin.

uv is used for all python-side dependencies (including dev deps).
Maturin is used only for building rust-side.

```bash
# To create .venv folder
uv venv
# Sync deps
uv sync --locked
# To build and install the package in a virtual environment
uv run -- maturin dev --uv
```

If you want to setup automatic rebuilds, use this command:

```bash
uv run -- python -m maturin_import_hook site install
```

It will force rebuild project when rust code changes.

For lints please use `pre-commit`.

```bash
pre-commit run -a
```
