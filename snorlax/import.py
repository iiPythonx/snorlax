# Copyright (c) 2026 iiPython

import asyncio
import json
import sys
from pathlib import Path

import aiohttp

from snorlax.database import VIDEO_COLUMNS

INSERT_COLUMNS = VIDEO_COLUMNS.get("insert")

async def main() -> None:
    client = aiohttp.ClientSession(base_url = "http://localhost:8000/v1/")

    # Loop over possible entries
    channel_cache: list[str] = []
    for item in Path(sys.argv[1]).glob("*.info.json"):
        metadata = json.loads(item.read_text())
        if metadata.get("_type") != "video":
            print(f"{item.name}: This file does not appear to be a YouTube video.")
            continue

        # Ensure channel exists
        if metadata["channel_id"] not in channel_cache:
            print(f"[C] [{metadata['uploader']}] (ID: {metadata['channel_id']})")
            async with client.post(
                "channel/create",
                json = {
                    "channel_id": metadata["channel_id"],
                    "name": metadata["uploader"],
                    "handle": metadata.get("uploader_id"),
                    "subscribers": metadata["channel_follower_count"]
                }
            ) as response:
                print(f"  - Status: {'created!' if response.status == 201 else 'already existed remotely'}")
                channel_cache.append(metadata["channel_id"])

        # Remap metadata
        import_metadata = {
            "caption_langs": [],  # Not supported for manual import, yet...
            "available": False
        }
        import_metadata |= {k: metadata.get(k, []) for k in INSERT_COLUMNS if k not in import_metadata}

        # Send video creation request
        print(f"[V] [{metadata['title']}] (ID: {metadata['id']})")
        async with client.post("video/create", json = import_metadata) as response:
            print(f"  - Asset {'created' if response.status == 201 else 'exists'} ✓")

        # Handle uploads
        async def upload_item(video_id: str, asset_type: str, local_file: Path) -> None:
            asset_name = "image" if asset_type == "cover.webp" else "video"
            async with client.head(f"assets/{metadata['channel_id']}/{metadata['id']}/{asset_type}") as response:
                if response.status != 404:
                    return print(f"  - {asset_name.capitalize()} exists ✓")

                print(f"  - Uploading {asset_name}...", end = "")
                with local_file.open("rb") as file:
                    data = aiohttp.FormData()
                    data.add_field("file", file, filename = asset_type)

                    response = await client.post(f"video/{video_id}/{asset_type}", data = data)
                    print(f" {'FAILED' if response.status != 200 else 'DONE'}!")

        # Check asset status
        normalized = item.with_name(item.name.split(".")[0])
        await upload_item(metadata["id"], "cover.webp", normalized.with_suffix(".webp"))
        await upload_item(metadata["id"], "video.mkv", normalized.with_suffix(".webm"))

    # Clean up
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
