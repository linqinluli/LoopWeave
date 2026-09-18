# FlexBackend report

FlexBackend is a training backend designed to coordinate model updates, sampling, adapter state, and evaluation through the LoopWeave service interface. It supports asynchronous operation and separates backend-specific execution from service-level scheduling.

## Design

The backend implements the shared training-backend interface. It initializes model resources, creates adapters, synchronizes weights, samples tokens, runs training steps, and releases adapter resources. The service layer owns request routing and lifecycle management; backend implementations own the execution details.

## Evaluation artifacts

The accompanying experiment directories retain the reported figures, tables, and numerical results. These artifacts should be interpreted using their stated labels and methodology; no result labels or values have been changed during anonymization.

## Reproducibility

Configurations and scripts under `paper_release/` document the experiment inputs and plotting workflow. Deployments require an environment with the relevant model, accelerator, and dependency resources.
