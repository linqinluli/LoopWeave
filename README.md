<div align="center">
  <img alt="LoopWeave Logo" src="docs/sphinx_doc/_static/logo_light.svg" width="400"/>
</div>

# LoopWeave

LoopWeave is a multi-tenant platform for fine-tuning and sampling language models on shared infrastructure through a unified service API.

## Installation

```bash
uv venv --python 3.12
uv sync --all-extras
python scripts/install_flash_attn.py
```

See [the example configuration](config/loopweave_config.example.yaml) for server settings, including model paths, persistence, and telemetry.

## Run the server

```bash
loopweave launch --port 10610 --config /path/to/loopweave_config.yaml
```

## Repository guide

- `src/loopweave/`: service implementation and backends.
- `config/`: example and evaluation configurations.
- `examples/`: client-side fine-tuning examples.
- `docs/sphinx_doc/source/`: user and developer documentation.
- `paper_release/`: experiment descriptions and associated artifacts.

## Architecture

LoopWeave provides a REST service for training and sampling. It manages sessions, LoRA adapters, model checkpoints, and optional telemetry while exposing a consistent API to compatible clients.

## License

See [LICENSE](LICENSE).
