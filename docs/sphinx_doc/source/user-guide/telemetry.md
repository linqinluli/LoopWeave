# Observability (OpenTelemetry)

LoopWeave includes optional **OpenTelemetry** integration for:

- **Traces** (distributed tracing across HTTP → controllers → Ray actors)
- **Metrics** (request/workflow + resource metrics)
- **Logs** (Python logging bridged into the OpenTelemetry log pipeline)

This document explains both **how to enable telemetry** and **how LoopWeave wires it internally** (what gets recorded, correlation keys, and how to extend instrumentation).

---

## Table of Contents

- [Quick start](#quick-start)
- [Exporters and configuration](#exporters-and-configuration)
- [What LoopWeave records](#what-loopweave-records)
  - [Traces](#traces)
  - [Metrics](#metrics)
  - [Logs](#logs)
- [Correlation / share keys](#correlation--share-keys)
- [Context propagation (Ray actors)](#context-propagation-ray-actors)
- [Developer guide](#developer-guide)
- [Recommended collector configuration](#recommended-collector-configuration)
- [Troubleshooting](#troubleshooting)
- [End-to-end example](#end-to-end-example)

---

## Quick start

Enable telemetry in `loopweave_config.yaml`:

```yaml
telemetry:
  enabled: true
  service_name: loopweave
  otlp_endpoint: http://localhost:4317
  resource_attributes:
    deployment.environment: production
    service.version: 1.0.0
```

> **Note**: `resource_attributes` allows you to attach custom metadata to all telemetry data. Common attributes include:
> - `deployment.environment`: e.g., `production`, `staging`, `development`
> - `service.version`: your application version
> - `service.namespace`: logical grouping of services
> - `host.name`: hostname of the machine
> - Custom attributes for your organization (e.g., `team`, `region`)

Alternatively set the endpoint via env var:

```bash
export LOOPWEAVE_OTLP_ENDPOINT=http://localhost:4317
```

Debug mode (prints to console exporters):

```bash
export LOOPWEAVE_OTEL_DEBUG=1
```

---

## Exporters and configuration

LoopWeave initializes OpenTelemetry providers at CLI startup and uses one of two exporter modes:

- **Console exporters** if `LOOPWEAVE_OTEL_DEBUG=1`
- **OTLP gRPC exporters** otherwise

The endpoint resolution order is:

1. `telemetry.otlp_endpoint` from config
2. `LOOPWEAVE_OTLP_ENDPOINT` environment variable
3. OpenTelemetry exporter default endpoint (if neither is provided)

LoopWeave exports:

- traces via `OTLPSpanExporter` (gRPC)
- metrics via `OTLPMetricExporter` (gRPC)
- logs via `OTLPLogExporter` (gRPC)

Resource metadata:

- `service.name` is set to `telemetry.service_name`
- additional resource attributes can be attached via `telemetry.resource_attributes`

---

## What LoopWeave records

### Traces

LoopWeave produces spans at several layers:

- **HTTP server spans**: FastAPI is instrumented when telemetry is enabled.
- **Controller spans**: training/sampling operations create spans such as:
  - `training_controller.create_model`
  - `training_controller.run_forward`
  - `training_controller.run_forward_backward`
  - `training_controller.run_optim_step`
  - `training_controller.save_checkpoint`
  - `sampling_controller.create_sampling_session`
  - `sampling_controller.run_sample`
  - `future_store.execute_operation`
- **Persistence spans**: Redis operations create spans such as:
  - `redis.SET`, `redis.GET`, `redis.DEL`, `redis.SCAN`
- **Backend / actor spans** (when running with Ray):
  - spans inside model actors (e.g. HuggingFace backend) are linked via propagated context
  - examples include `hf_model.forward_backward`, `hf_model.optim_step`, `hf_model.save_state`, etc.

LoopWeave attaches key identifiers as span attributes (see [Correlation / share keys](#correlation--share-keys)).

### Metrics

LoopWeave emits two broad categories of metrics:

#### 1) Workflow metrics (counters/histograms)

Examples (names are stable and can be used as dashboards/alerts):

- Training:
  - `loopweave.training.models.active` (up/down counter)
  - `loopweave.training.tokens_per_second` (histogram)
  - `loopweave.training.checkpoints.saved` (counter)
  - `loopweave.training.checkpoint.size_bytes` (histogram)
- Sampling:
  - `loopweave.sampling.sessions.active` (up/down counter)
  - `loopweave.sampling.requests` (counter)
  - `loopweave.sampling.duration` (histogram, seconds)
  - `loopweave.sampling.tokens_per_second` (histogram)
  - `loopweave.sampling.output_tokens` (histogram)
- Futures:
  - `loopweave.futures.queue_length` (up/down counter)
  - `loopweave.futures.created` (counter)
  - `loopweave.futures.completed` (counter)
  - `loopweave.futures.wait_time` (histogram)
  - `loopweave.futures.execution_time` (histogram)
- Persistence:
  - `loopweave.redis.operation.duration` (histogram)

Many metrics include attributes such as `base_model`, `operation_type`, `model_id`, or `queue_state` to support filtering and grouping.

#### 2) Resource metrics (observable gauges)

When telemetry is enabled, LoopWeave starts a background resource collector that exports observable gauges such as:

- CPU:
  - `loopweave.resource.cpu.utilization_percent`
- Memory:
  - `loopweave.resource.memory.used_bytes`
  - `loopweave.resource.memory.total_bytes`
  - `loopweave.resource.memory.utilization_percent`
- GPU (if NVML is available):
  - `loopweave.resource.gpu.utilization_percent` (with attribute `gpu_id`)
  - `loopweave.resource.gpu.memory_used_bytes` (with attribute `gpu_id`)
  - `loopweave.resource.gpu.memory_total_bytes` (with attribute `gpu_id`)
- Process:
  - `loopweave.resource.process.memory_used_bytes`

### Logs

LoopWeave bridges Python logging into OpenTelemetry:

- log records are exported via the configured OTel log provider
- existing logging handlers are not removed (OTel handler is added)

---

## Correlation / share keys

LoopWeave is multi-tenant and multi-client. To make traces searchable and linkable across components, LoopWeave sets a small set of **high-signal attributes** on spans.

You can treat these as "share keys" in your observability backend:

- `loopweave.session_id`
  - links a user session across training + sampling activity
- `loopweave.training_run_id`
  - links all spans for a specific training run (LoRA adapter lifecycle)
- `loopweave.sampling_session_id`
  - links all spans for a specific sampling session
- `loopweave.request_id`
  - links FutureStore execution spans with the async future lifecycle
- `loopweave.operation_type`
  - categorizes futures (e.g. `forward_backward`, `optim_step`, `sample`)
- (additional common attributes)
  - `loopweave.base_model`
  - `loopweave.lora_rank`
  - `loopweave.backward`

For practical examples of filtering traces by these keys in an observability backend, see the [End-to-end example](#end-to-end-example) section.

---

## Context propagation (Ray actors)

When LoopWeave executes work inside Ray actors, it propagates the OpenTelemetry context explicitly:

- At the controller/backend boundary, LoopWeave **injects** the current trace context into a serializable dict.
- The Ray actor side **extracts** that context and starts child spans under that context.

This provides end-to-end traces that cross process boundaries even when Ray scheduling changes the execution location.

---

## Developer guide

### Creating spans

Use `get_tracer()` and standard OpenTelemetry span APIs:

```python
from loopweave.telemetry.tracing import get_tracer

tracer = get_tracer("loopweave.my_module")
with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("loopweave.session_id", session_id)
    span.set_attribute("loopweave.training_run_id", training_run_id)
    # ... your logic ...
```

### Recording metrics

Use the centralized metrics registry:

```python
from loopweave.telemetry.metrics import get_metrics

metrics = get_metrics()
metrics.futures_created.add(1, {"operation_type": "forward_backward"})
metrics.futures_execution_time.record(0.123, {"operation_type": "forward_backward"})
```

### Choosing attributes

Prefer:

- stable identifiers (`session_id`, `training_run_id`, `sampling_session_id`, `request_id`)
- low-cardinality labels for metrics (e.g. `base_model`, `operation_type`, `queue_state`)

Avoid putting user prompts or raw payloads into span attributes.

---

## Recommended collector configuration

LoopWeave exports OTLP over **gRPC** by default. We recommend running an OpenTelemetry Collector (or an observability backend that provides an OTLP receiver) listening on the configured `otlp_endpoint` (commonly `4317`).

At minimum, ensure:

- the collector has an **OTLP receiver** enabled (gRPC)
- traces/metrics/logs pipelines are configured to accept OTLP and forward to your backend (Jaeger/Tempo, Prometheus, SigNoz, etc.)

LoopWeave-specific knobs:

- set `telemetry.service_name` to a stable value (e.g. `loopweave-prod`)
- use `telemetry.resource_attributes` to tag deployments (e.g. environment, region, version)

---

## Troubleshooting

### No telemetry shows up

- Ensure `telemetry.enabled: true`.
- Ensure the OTLP endpoint is reachable from the LoopWeave server process.
- Try debug mode to confirm instrumentation works:

```bash
export LOOPWEAVE_OTEL_DEBUG=1
```

### GPU metrics missing

- GPU gauges require NVML (`pynvml`) and a working NVML environment. LoopWeave will gracefully skip GPU metrics if unavailable.

---

## End-to-end example

This section demonstrates running LoopWeave with an observability backend. We use [SigNoz](https://signoz.io/) in this example because it provides a unified backend for traces, metrics, and logs in a single platform, making it easy to demonstrate all three observability pillars together.

> **Alternative backends**: LoopWeave exports standard OTLP data and works with any OpenTelemetry-compatible backend:
> - **Traces**: Jaeger, Zipkin, Tempo, Datadog, etc.
> - **Metrics**: Prometheus (via OTLP or Prometheus exporter), Grafana Mimir, etc.
> - **Logs**: Loki, Elasticsearch, etc.
>
> Simply point `telemetry.otlp_endpoint` to your preferred collector or backend.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed

### Step 1: Start SigNoz

We recommend installing SigNoz using Docker Compose as shown below. For alternative installation methods (install script, Docker Swarm, Kubernetes, etc.), refer to the [SigNoz installation guide](https://signoz.io/docs/install/).

```bash
git clone -b main https://github.com/SigNoz/signoz.git && cd signoz/deploy/docker
docker compose up -d --remove-orphans
```

SigNoz will start with an OTLP receiver on `localhost:4317`.

### Step 2: Configure LoopWeave

Add the following telemetry configuration to your `loopweave_config.yaml`:

```yaml
telemetry:
  enabled: true
  service_name: loopweave
  otlp_endpoint: http://localhost:4317
  resource_attributes:
    deployment.environment: demo
```

### Step 3: Launch LoopWeave and run workloads

```bash
loopweave launch --config /path/to/loopweave_config.yaml
```

Run some training or sampling operations through the LoopWeave client to generate telemetry data.

### Step 4: View in SigNoz

Open SigNoz at `http://localhost:8080` to explore the collected telemetry data.

#### Traces

LoopWeave attaches structured correlation keys to every span, enabling powerful filtering in the Traces Explorer.

**Filter by `loopweave.session_id`** — track all tasks within a single session. By filtering on a specific `loopweave.session_id`, the Explorer surfaces every span across both training and sampling operations initiated in that session, providing a holistic view of all session-level activity:


**Filter by `loopweave.training_run_id`** — track all tasks belonging to a specific training client. Filtering by `loopweave.training_run_id` isolates the full lifecycle of a specific training client, showing training operations such as `run_forward_backward`, `run_optim_step`, and `save_checkpoint` along with their execution order:


**Filter by `loopweave.sampling_session_id`** — track all tasks belonging to a specific sampling client. Filtering by `loopweave.sampling_session_id` narrows the view to spans from a single inference session, such as `sampling_controller.run_sample` and `sampling_controller.create_sampling_session`:


**Inspect a single HTTP request trace** — all spans generated during one HTTP request share the same trace ID, allowing you to view the complete execution path of that request. The flamegraph below shows the span tree from HTTP receive through internal processing, state persistence, and backend execution:


#### Logs

Every log entry emitted by LoopWeave is automatically correlated with a **span ID** and **trace ID**. You can use these two identifiers to pinpoint the exact operation step a log belongs to, or navigate in reverse — from a span to all logs produced during that operation:


#### Metrics

All metrics emitted by LoopWeave can be browsed in the SigNoz Metrics page, which lists every metric along with its type, unit, and sample count:


You can also configure custom panels in the SigNoz Dashboard to monitor specific metrics. Below are two example panel configurations for training throughput and sampling QPS; additional panels can be created to suit your specific monitoring needs.

**Training throughput (tokens/s)** — a dashboard panel querying `loopweave.training.tokens_per_second` with P50 aggregation, grouped by `base_model`, to monitor training efficiency over time:


**Sampling request rate (QPS)** — a dashboard panel querying `loopweave.sampling.requests` with Rate aggregation, grouped by `base_model`, to monitor inference throughput and detect traffic spikes:

