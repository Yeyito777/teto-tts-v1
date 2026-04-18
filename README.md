# teto-tts-v1

A minimal local TTS wrapper for a Teto-style voice using MioTTS 0.1B on CPU.

Canonical interface:
- `./tts load`
- `./tts "things to say"`
- `./tts unload`

Behavior:
- `tts load` starts the local background services and keeps the model warm
- `tts "..."` synthesizes with the hardcoded preset `jamie-spoken-for-20s-40s`
- `tts unload` stops the local services

Outputs:
- wavs are written to `outputs/`
- latest output is symlinked as `outputs/latest.wav`

Project notes:
- the local preset/ref/model/binaries are intentionally not committed
- the public repo tracks only the code and project structure
