# Sunstone Switch

Full-colour **Python 3** neon three-rail junction arcade for **ElbowOS**.

Featured account: [https://x.com/ElbowOS](https://x.com/ElbowOS)

Reel (9:16 MP4): [Google Drive](https://drive.google.com/file/d/1hGs9bZKmAxGKQVhdFpAAlhVKXPBa_OU6/view?usp=drivesdk)

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sunstone_switch.py --play
```

- **A / D** or arrows — switch rails
- **R** — reset
- **Esc** — quit

Collect gold orbs and magenta gates. Dodge slag spikes. Speed climbs with distance.

## Record a 15s 1080×1920 reel

```bash
python3 sunstone_switch.py --record
```

Needs `ffmpeg` on PATH. Output defaults to `/home/workdir/artifacts/SUNSTONE_SWITCH_ElbowOS.mp4`.
