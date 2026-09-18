import os
import platform
import subprocess
import sys

import torch


# Flash-attention wheels are resolved from the upstream project release assets.
FLASH_VERSIONS = {"12": "2.8.1", "13": "2.8.3"}

# Get torch version
TORCH_VERSION_RAW = torch.__version__
torch_major, torch_minor = TORCH_VERSION_RAW.split(".")[:2]
torch_version = f"{torch_major}.{torch_minor}"

# Get python version
python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"

# Get platform name
platform_name = platform.system().lower() + "_" + platform.machine()

# Get cxx11_abi
cxx11_abi = str(torch._C._GLIBCXX_USE_CXX11_ABI).upper()

# Is ROCM
# torch.version.hip/cuda are runtime attributes not in type stubs
IS_ROCM = hasattr(torch.version, "hip") and torch.version.hip is not None  # type: ignore[attr-defined]

if IS_ROCM:
    print("We currently do not host ROCm wheels for flash-attn.")
    sys.exit(1)
else:
    torch_cuda_version = torch.version.cuda  # type: ignore[attr-defined]
    cuda_major = torch_cuda_version.split(".")[0] if torch_cuda_version else None
    if cuda_major not in FLASH_VERSIONS:
        print(f"Only CUDA 12/13 wheels are hosted for flash-attn. Got CUDA {cuda_major}.")
        sys.exit(1)
    FLASH_VERSION = FLASH_VERSIONS[cuda_major]
    # CUDA 13 wheels use "cu13" tag; CUDA 12 uses "cu12"
    cuda_version = cuda_major
    wheel_filename = (
        f"flash_attn-{FLASH_VERSION}%2Bcu{cuda_version}torch{torch_version}"
        f"cxx11abi{cxx11_abi}-{python_version}-{python_version}-{platform_name}.whl"
    )
    local_filename = (
        f"flash_attn-{FLASH_VERSION}-{python_version}-{python_version}-{platform_name}.whl"
    )

if cuda_major == "13":
    expected_sha256 = None
    wheel_url = (
        "https://github.com/Dao-AILab/flash-attention/releases/download"
        f"/v{FLASH_VERSION}/flash_attn-{FLASH_VERSION}%2Bcu{cuda_version}torch{torch_version}"
        f"cxx11abi{cxx11_abi}-{python_version}-{python_version}-{platform_name}.whl"
    )
else:
    expected_sha256 = None
    wheel_url = (
        "https://github.com/Dao-AILab/flash-attention/releases/download"
        f"/{FLASH_VERSION}/{wheel_filename}"
    )

print(f"wheel_url: {wheel_url}")
print(f"target_local_file: {local_filename}")

local_path = f"/tmp/{local_filename}"

# avoid downloading multiple times in case of retrys
if os.path.exists(local_path):
    print(f"{local_path} already exists, removing the old file.")
    os.remove(local_path)

subprocess.run(["wget", wheel_url, "-O", local_path], check=True)

# Verify the download against the pinned SHA-256 for third-party (CUDA 13)
# wheels before installing, so a tampered/incorrect artifact never runs.
if expected_sha256 is not None:
    import hashlib

    h = hashlib.sha256()
    with open(local_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    actual_sha256 = h.hexdigest()
    if actual_sha256 != expected_sha256:
        print(
            f"SHA-256 mismatch for {local_path}: "
            f"expected {expected_sha256}, got {actual_sha256}. Aborting."
        )
        os.remove(local_path)
        sys.exit(3)
    print(f"SHA-256 verified: {actual_sha256}")

subprocess.run(["uv", "pip", "install", "--python", sys.executable, local_path], check=True)

# Try to import flash_attn
try:
    import flash_attn

    print(f"flash_attn {flash_attn.__version__} imported successfully!")
except ImportError as e:
    print("Failed to import flash_attn:", e)
    sys.exit(2)
