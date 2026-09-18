# Embedded Mode

## Background

LoopWeave is designed to serve as a **transparent compute service layer** for RL training frameworks like Trinity and veRL. In production, LoopWeave typically runs as a standalone daemon (`loopweave launch`), and users must:

1. Write a `loopweave_config.yaml` configuration file
2. Manually start the server with `loopweave launch --config ...`
3. Set the `TINKER_BASE_URL` environment variable for clients to connect

This manual setup creates friction, especially for:
- **RL framework users** who just want to run training scripts without learning LoopWeave internals
- **Development/debugging** workflows where quick iteration is key
- **CI pipelines** that need reproducible, self-contained environments

**Embedded mode** solves this by providing a `loopweave.init()` API — similar to `ray.init()` — that handles service discovery, configuration generation, startup, and connection automatically.

## Two Modes of Operation

| | Daemon Mode | Embedded Mode |
|---|---|---|
| How to start | `loopweave launch --config ...` | `loopweave.init(model=...)` |
| Lifecycle | Independent process, manually managed | Follows main process, auto-cleanup via atexit |
| Best for | Production deployments, multi-user shared clusters | Dev/debug, training scripts, CI |
| Service discovery | User sets `TINKER_BASE_URL` manually | Automatic (env var → address file → process scan → default port) |

**Both modes coexist**: `loopweave.init()` first tries to discover an existing daemon. Only when no running service is found does it start an embedded instance.

## Quick Start

```python
import loopweave

# Initialize LoopWeave — auto-discovers existing service or starts one
loopweave.init(model="/path/to/Qwen2.5-0.5B-Instruct")

# Use the service client for training
training_client = loopweave.create_training_client(
    base_model="Qwen2.5-0.5B-Instruct",
    rank=8,
)
# ... your training loop ...

# Optional: explicit shutdown (atexit handles this automatically)
loopweave.shutdown()
```

### Other `init()` patterns

```python
# Connect to a specific running server
loopweave.init(address="http://gpu-cluster:10610")

# Use an existing config file
loopweave.init(config="/path/to/loopweave_config.yaml")

# No arguments — relies on env vars or default config file
loopweave.init()

# Get a service client (auto-inits if not already done)
service_client = loopweave.get_service_client()
```

## Service Discovery Priority

When `loopweave.init()` is called, it tries to find an existing service in this order:

1. `address=...` argument passed to `init()`
2. `LOOPWEAVE_ADDRESS` environment variable
3. Address file at `~/.loopweave/loopweave_current_server`
4. Process scan (looks for running `loopweave launch` or `uvicorn` processes)
5. Default port probe: `http://127.0.0.1:10610`

If no service is found, embedded mode starts a new one using configuration from:

1. `config=...` argument passed to `init()`
2. `LOOPWEAVE_CONFIG` environment variable
3. `model=...` argument → auto-generates minimal config
4. `LOOPWEAVE_MODEL_PATH` environment variable → auto-generates minimal config
5. Default config file: `~/.loopweave/configs/loopweave_config.yaml`
6. None available → raises `RuntimeError` with helpful guidance

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOOPWEAVE_ADDRESS` | Address of running LoopWeave service | — |
| `LOOPWEAVE_API_KEY` | API authentication key | Auto-generated |
| `LOOPWEAVE_CONFIG` | Path to configuration file | — |
| `LOOPWEAVE_MODEL_PATH` | Model path for auto-config generation | — |
| `LOOPWEAVE_ENABLE_AUTO_CONNECT` | Enable auto-connect in `get_service_client()` | `"1"` |
| `LOOPWEAVE_HOME` | LoopWeave home directory | `~/.loopweave` |
| `LOOPWEAVE_HOST` | Server bind address | `127.0.0.1` |
| `LOOPWEAVE_PORT` | Server bind port | `10610` |

## Lifecycle

- **Embedded services** are tied to the main process. When the Python process exits (normally or via signal), the embedded LoopWeave server is automatically terminated via `atexit`.
- **Daemon services** (`loopweave launch`) are independent and persist until manually stopped.
- `loopweave.shutdown()` can be called explicitly to stop an embedded service early.
- `loopweave.init()` is **idempotent** — calling it multiple times is safe (no-op after first success).

## Integration with RL Frameworks

For framework integrations (e.g., Trinity), the pattern is:

```python
import loopweave

# In your framework's initialization code:
loopweave.init(model=model_path, ignore_reinit_error=True)
service_client = loopweave.get_service_client()

# Use service_client as before...
```

This requires no changes to the user's workflow — the framework handles LoopWeave setup transparently.
