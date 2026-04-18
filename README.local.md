# teto-tts-v1

Canonical interface:
- `./tts load`
- `./tts "things to say"`
- `./tts unload`

Behavior:
- `tts load` starts the local CPU stack in the background
- `tts "..."` synthesizes with the hardcoded preset `jamie-spoken-for-20s-40s`, saves a wav under `outputs/`, and plays it with `mpv` if available
- `tts unload` stops the background services

Rules:
- `load` fails if already loaded
- speaking fails if not loaded
- `unload` fails if not loaded

Useful local assets:
- chosen preset: `refs/presets/jamie-spoken-for-20s-40s.pt`
- chosen ref wav: `refs/chosen-ref.wav`
- extra ref material: `refs/candidates/`
