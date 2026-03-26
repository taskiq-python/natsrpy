[![PyPI](https://img.shields.io/pypi/v/natsrpy?style=for-the-badge)](https://pypi.org/project/scyllapy/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/natsrpy?style=for-the-badge)](https://pypistats.org/packages/scyllapy)

# Nats client

This is a client library for [NATS](https://nats.io) written in rust.

## Sponsors of this project

Special thanks to [Intree](https://intree.com) for supporting development of this project.

## installation

This package can be installed from pypi:

```bash
pip install natsrpy
```

Or alternatively you can build it yourself using maturin, and stable rust.

## Usage

You can see usage examples in our [examples](https://github.com/taskiq-python/natsrpy/tree/master/examples) folder.

Also, our [tests](https://github.com/taskiq-python/natsrpy/tree/master/python/tests)
are written in python and could be a good place to discover features and the way they intended to be used.

As of for now, our documentation is only availabe in source code. You can see it in our [type-stubs folder](https://github.com/taskiq-python/natsrpy/tree/master/python/natsrpy/_natsrpy_rs).

## Development

We use stable rust and pyo3 for writing python extension module.

In order to run the project use maturin:

```bash
# To create .venv folder
uv venv
# To build and install the package in a virtual environment
maturin dev --uv
```

For lints please use `pre-commit`.

```bash
pre-commit run -a
```
