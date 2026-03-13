# Snorlax

### Running

```sh
uv pip install .
uv run uvicorn snorlax:app
```

### Configuration

All configuration data for Snorlax is stored in `snorlax.toml`.  

Right now, you can edit:
- `snorlax.database_path`
- `snorlax.video_path`
- `videos.subtitle_languages`
    - List of [yt-dlp](https://github.com/yt-dlp/yt-dlp) compatible subtitle formats, regex supported.
    - See [this issue](https://github.com/yt-dlp/yt-dlp/issues/9371#issuecomment-1978969330) for more information.

### ID System

Snorlax supports both types of YouTube IDs, including the real channel ID (`UC.*`) as well as a handle (`@iiPythonx`).  
The UI will attempt to link to the handle if present, otherwise it will fall back to the official ID. 

Note that if you download a song from a music channel, it will not have a handle.  
An "official music video" from the same "channel" will also have a different channel ID, resulting in two channels listed in Snorlax with the same name.

This name duplication shouldn't be a problem though, other then making the channel list feel a bit more cluttered.

### API

```
/v1/videos
/v1/channels
/v1/video/VIDEO_ID
/v1/channel/CHANNEL_ID
/v1/jobs
/v1/search
```

### Screenshot

![Snorlax Screenshot](.github/1.png)

### Roadmap

- [x] Migrate /watch to an API endpoint, with JS-based humanize
- [x] Migrate the ingest methods to custom API endpoints
- [ ] Ability to set video expiration time, turning Snorlax into something like [cobalt](https://cobalt.tools/)
- [x] Search mechanism for ~~channels and~~ videos
