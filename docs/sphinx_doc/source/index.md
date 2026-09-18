---
sd_hide_title: true
---

# LoopWeave

<div class="hero-logo" align="center">
  <img class="only-light" src="_static/logo_light.svg" alt="LoopWeave Logo" width="280"/>
  <img class="only-dark" src="_static/logo_dark.svg" alt="LoopWeave Logo" width="280"/>
</div>

<p class="hero-subtitle"><strong>LoopWeave</strong> is a multi-tenant platform that lets multiple users fine-tune LLMs on shared infrastructure through a unified API.</p>

<div class="install-command">

<p class="install-title">Quick Install</p>

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/anonymous/loopweave/main/scripts/install.sh)"
```

<p class="install-more-link">For more installation options (PyPI, source, Docker), see the <a href="getting-started/installation.html">Installation Guide</a>.</p>

</div>

<div class="quickstart-cta">
  <a class="quickstart-cta-link" href="getting-started/quickstart.html">Quickstart →</a>
</div>

```{admonition} 🚀 No GPU? No problem!
:class: tip

You don't need to own a GPU to run LoopWeave. Deploy it to a pay-as-you-go cloud provider —
**[Modal](deployment/modal.md)** (serverless, scale-to-zero) or
**[Lambda Cloud](deployment/lambda.md)**, then fine-tune from your laptop.
See the **[Deployment guides](deployment/index.md)**.
```

```{toctree}
:maxdepth: 2
:hidden:

getting-started/index
deployment/index
user-guide/index
development/index
```
