# Multi-tenant training simulator

This directory contains a simulator for studying multi-tenant training workloads. It models request arrival, sampling, training, evaluation, scheduling, and resource usage through a common asynchronous backend interface.

## Components

- `orchestrator.py` coordinates tenants and workload events.
- `backend/` defines the training backend interface and simulator implementations.
- `configs/` contains example workload configurations.
- `data/` contains input metadata and result artifacts.

## Backend interface

Backends provide asynchronous methods for initialization, adapter creation, weight synchronization, sampling, training steps, tokenization, and cleanup. The simulator records wall-clock time, training progress, sample counts, staleness, latency, rewards, and evaluation curves.

## Data references

The included configurations may reference public model and dataset identifiers. These references are retained as third-party dependencies and do not identify the authors or host environment.

## Outputs

Runs produce JSON summaries per tenant, including final accuracy, reward and evaluation curves, completed training steps, sample totals, mean staleness, and mean sampling latency.
