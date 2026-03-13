# Nats client

This is a client library for [NATS](https://nats.io) written in rust.

Credits for [Intree](https://intree.com) for supporting this project.


## installation

This package can be installed from pypi:

```bash
pip install natsrpy
```

Or alternatively you ca build it yourself using maturin, and stable rust.

## Development

We use stable rust and pyo3 for writing python extension module. 

In order to run the project use maturin:

```bash
# To create .venv folder
uv venv
# To build and install the package in a virtual environment
maturin dev --uv
```
