"""Step 1: download Arabic auto-captions + metadata for every video in the playlist.

For each video we save two files in data/raw/:
    <video_id>.ar.vtt   the raw captions
    <video_id>.json     video_id, title, upload_date, url
"""
import json

import yt_dlp

import config


def list_video_ids(playlist_url):
    """Return the video IDs in the playlist (fast: doesn't open each video)."""
    options = {"extract_flat": True, "quiet": True}
    with yt_dlp.YoutubeDL(options) as ydl:
        playlist = ydl.extract_info(playlist_url, download=False)
    return [entry["id"] for entry in playlist["entries"]]


def download_episode(video_id):
    """Download captions + metadata for one video. Returns True on success."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    options = {
        "skip_download": True,                  # no video, no audio
        "writeautomaticsub": True,              # auto-generated captions
        "subtitleslangs": [config.CAPTION_LANG],
        "subtitlesformat": "vtt",
        "outtmpl": str(config.RAW_DIR / "%(id)s"),
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

    # Some videos have no Arabic auto-captions: then no .vtt file appears.
    vtt_path = config.RAW_DIR / f"{video_id}.{config.CAPTION_LANG}.vtt"
    if not vtt_path.exists():
        print(f"  no {config.CAPTION_LANG} captions, skipping")
        return False

    date = info["upload_date"]  # looks like "20240315"
    metadata = {
        "video_id": video_id,
        "title": info["title"],
        "upload_date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
        "url": url,
    }
    json_path = config.RAW_DIR / f"{video_id}.json"
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main():
    if not config.PLAYLIST_URL:
        raise SystemExit("PLAYLIST_URL is missing. Add it to your .env file.")

    config.RAW_DIR.mkdir(parents=True, exist_ok=True)

    video_ids = list_video_ids(config.PLAYLIST_URL)
    print(f"Found {len(video_ids)} videos in the playlist")

    for number, video_id in enumerate(video_ids, start=1):
        # The .json file is written last, so if it exists the episode is complete.
        if (config.RAW_DIR / f"{video_id}.json").exists():
            print(f"[{number}/{len(video_ids)}] {video_id}: already downloaded")
            continue

        print(f"[{number}/{len(video_ids)}] {video_id}: downloading")
        try:
            download_episode(video_id)
        except Exception as error:  # one bad video shouldn't stop the whole run
            print(f"  failed: {error}")


if __name__ == "__main__":
    main()
