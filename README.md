# Demo Website

## Quick Start

### Phase 1: Static Demo (No GPU needed)

```bash
cd demo-website
python -m http.server 8080
# Open http://localhost:8080
```

### Phase 2: Interactive Demo (GPU needed, e.g. DSW)

```bash
# 1. Install dependencies
pip install fastapi uvicorn websockets aiofiles pillow numpy

# 2. Put your demo videos in static/videos/
#    Then uncomment the <video> tags in index.html

# 3. Start server
python server.py

# 4. Access via DSW port forwarding or directly at http://localhost:8080
```

### DSW Deployment

1. Upload `demo-website/` folder to DSW
2. Open DSW terminal
3. `cd demo-website && python server.py`
4. In DSW console, find "Custom Service" or port forwarding, expose port 8080
5. Access the URL provided by DSW

### Integrate Your Model

Edit `server.py`, replace `DummyPipeline` with your real model:

```python
class StreamingPipeline:
    def __init__(self):
        self.model = load_your_model()
        self.vae = load_vae()

    def set_prompt(self, prompt):
        self.text_emb = self.model.encode_text(prompt)

    def generate_next_frame(self, keyboard, mouse):
        latent = self.model.generate(keyboard, mouse, self.text_emb)
        frame = self.vae.decode(latent)
        # encode to JPEG and return bytes
        ...
```

## File Structure

```
demo-website/
  index.html       # Main webpage (frontend)
  server.py        # Backend server (FastAPI + WebSocket)
  static/
    videos/        # Put your demo .mp4 files here
  README.md
```
