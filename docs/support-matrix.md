# Provisional Mac Support Matrix

Status: incomplete; not a release support claim.

The first release targets Apple Silicon Macs. Current thresholds are deliberately provisional until repeatable model and concurrency benchmarks exist across representative hardware.

| Profile | Memory | Free disk | Model class | Evidence status |
|---|---:|---:|---|---|
| Apple Silicon 16 GB | 16 GiB minimum | 40 GiB | Small | Configuration only; benchmark missing |
| Apple Silicon 32 GB | 32 GiB minimum | 80 GiB | Medium | Configuration only; benchmark missing |
| Apple Silicon 64 GB+ | 64 GiB minimum | 120 GiB | Large | Configuration only; benchmark missing |

## Interpretation

- A successful preflight means the machine matches a provisional resource profile. It does not prove acceptable model quality, speed, concurrency, thermal behavior, or full four-component compatibility.
- An `unknown` result means a required measurement could not be read and must not be presented as unsupported hardware.
- An `unsupported` result means a declared blocker was observed, such as non-arm64 architecture, insufficient resources, or required port collision.
- Minimum macOS remains undecided until the live requirements of all four upstream projects are verified.

## Required evidence before release

- At least one clean environment for every supported profile.
- oMLX model load, first-token latency, sustained throughput, memory pressure, and concurrent-agent measurements.
- Semantica, holaOS, and Herdr compatibility on the same profile.
- Sleep/wake, restart, low-disk, high-memory-pressure, and upgrade behavior.
- Download size, installed footprint, and uninstall recovery measurements.
