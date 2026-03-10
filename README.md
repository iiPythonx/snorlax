# Snorlax

### Running

```sh
uv pip install .
uv run uvicorn snorlax:app
```

### Management

Replicate a video from YouTube into Snorlax:

```sh
curl -X POST http://localhost:8000/download/video/YT_VIDEO_ID
```

Replicate a channel from YouTube into Snorlax:

```sh
curl -X POST http://localhost:8000/download/channel/YT_CHANNEL_ID
```

> [!NOTE]
> These endpoints are subject to change as the API develops.

### Screenshot

![Snorlax Screenshot](.github/1.png)

### Roadmap

- [ ] Migrate /watch to an API endpoint, with JS-based humanize
- [ ] Migrate the ingest methods to custom API endpoints
