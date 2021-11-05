import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import cache, partial

import pafy
import youtube_dl

with open("nemo/data/streams.json") as json_file:
    streams = json.load(json_file)

original_time = datetime.now()
CACHE_TTL = 19800  # Cache TTL in sec


@cache
def pafy_worker(category: str, video_id: str):
    video_url = f"http://www.youtube.com/watch?v={video_id}"
    video = pafy.new(video_url, basic=False, gdata=False, size=False)
    best = video.getbestaudio()
    playurl = best.url
    return {
        "category": category,
        "title": video._title,
        "author": video._author,
        "id": video.videoid,
        "duration": video.duration,
        "url": playurl,
        "expiry": video.expiry,
    }


def check_cache_expiry():
    current_time = datetime.now()
    diff = current_time - original_time
    return diff.total_seconds() >= CACHE_TTL


def reset_cache_time():
    global original_time
    original_time = datetime.now()


def update_cache():
    clear_streams_cache()
    for k in streams.keys():
        video_urls = streams[k]
        max_workers = 10
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            some_func = partial(pafy_worker, k)
            executor.map(some_func, video_urls)
    reset_cache_time()


def get_all_streams(category):
    if category not in streams.keys():
        return {
            "message": "Invalid category: {}. Should be one of {}".format(
                category, list(streams.keys())
            )
        }

    video_urls = streams[category]
    max_workers = 5
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        some_func = partial(pafy_worker, category)
        result = list(executor.map(some_func, video_urls))

    return result


def get_stream_by_id(category: str, id: str):
    return pafy_worker(category=category, video_id=id)


def clear_streams_cache():
    pafy_worker.cache_clear()
    with youtube_dl.YoutubeDL({}) as ydl:
        ydl.cache.remove()


update_cache()
