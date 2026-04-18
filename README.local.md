# teto-tts-v1

Local productionized MioTTS 0.1B CPU setup for a Teto-style voice.

What is included:
- MioTTS-Inference app code
- helper scripts to start the local CPU stack
- ref-management scripts
- project layout for refs, presets, models, and outputs

What is intentionally not committed:
- model weights
- vendored llama.cpp binaries
- virtualenv
- generated outputs
- copyrighted/audio reference assets

Canonical local layout:
- model: `models/MioTTS-GGUF/MioTTS-0.1B-BF16.gguf`
- chosen ref: `refs/chosen-ref.wav`
- chosen preset id: `jamie-spoken-for-20s-40s`

Start locally:
1. `scripts/start-llm-cpu.sh`
2. `scripts/start-api-cpu.sh`
