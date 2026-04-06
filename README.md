# Snorlax

### Running

Build the frontend:
```sh
bun i
bun run build
```

Launch the backend:
```sh
uv pip install .
uv run uvicorn snorlax:app
```

You can also run the frontend in development mode via `bun dev`.

### Configuration

All configuration data for Snorlax is stored in `snorlax.toml`. Right now, you can edit:
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

Current API version is v1, docs available [here](.github/docs/v1.md).

### Screenshot

![Snorlax Screenshot](.github/1.png)

### Roadmap

Current features:
- Browsing videos and channels
- Adding, viewing, removing jobs from the management menu
- Settings page with support for automatic subtitles, autoplay, sponsorblock, and progress saving
- Endpoints and buttons for removing videos and channels
- Job system integrated into database for persistence, with auto restart if the server reboots or something mid-way
- Somewhat robust database with all the data you could want
- Video.js based web player with support for captions/subtitles **AND** chapters
- API that doesn't suck, complete with full pagination

Planned at some point:

- [ ] Ability to set video expiration time, turning Snorlax into something like [cobalt](https://cobalt.tools/)
- [ ] Search channels in addition to videos
- [ ] Browse page for videos, that has sorting options by likes, views, etc.
    - [ ] Filtering (by channel, by date range, etc.)

Suggesting features can be done by [opening an issue](https://github.com/iipythonx/snorlax/issues/new).
