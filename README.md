# Snorlax

### Running

```sh
uv pip install .
uv run uvicorn snorlax:app
```

### Management

Head to `/manage` and you can add a import job, which currently supports both videos and channels.

### API

```
/v1/videos
/v1/channels
/v1/video/VIDEO_ID
/v1/channel/CHANNEL_ID
/v1/jobs
```

### Screenshot

![Snorlax Screenshot](.github/1.png)

### Roadmap

- [x] Migrate /watch to an API endpoint, with JS-based humanize
- [x] Migrate the ingest methods to custom API endpoints
