#!/usr/bin/env python3
"""Build a resumable, locally stored Wikipedia/Wikimedia photo pack."""
import csv
import html
import json
import mimetypes
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA_JS = ROOT / "travel-data.js"
PHOTO_JS = ROOT / "travel-photos.js"
IMAGE_DIR = ROOT / "images"
MISSING_CSV = ROOT / "places-without-photos.csv"
USER_AGENT = "TravelQuizPersonalPhotoPack/1.0 (local personal quiz; Wikimedia API client)"
MIN_API_INTERVAL = 3.2
last_api_request = 0.0


def read_js_data(path, symbol):
    source = path.read_text(encoding="utf-8")
    match = re.search(rf"window\.{symbol}\s*=\s*(.*);\s*$", source, re.S)
    if not match:
        raise ValueError(f"Could not read {symbol} from {path}")
    return json.loads(match.group(1))


def write_manifest(manifest):
    PHOTO_JS.write_text(
        "window.TRAVEL_PHOTOS = " + json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )


def get_json(endpoint, params):
    global last_api_request
    wait = MIN_API_INTERVAL - (time.monotonic() - last_api_request)
    if wait > 0:
        time.sleep(wait)
    last_api_request = time.monotonic()
    request = Request(endpoint + "?" + urlencode(params), headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            return json.load(response)
    except HTTPError as exc:
        if exc.code == 429:
            retry_after = exc.headers.get("Retry-After", "60")
            try:
                delay = max(30.0, float(retry_after))
            except ValueError:
                delay = 60.0
            print(f"Wikimedia rate limit; waiting {delay:.0f} seconds before resuming.", flush=True)
            time.sleep(delay)
            last_api_request = time.monotonic()
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        raise


def clean_metadata(value):
    if not value:
        return ""
    raw = value.get("value", "") if isinstance(value, dict) else str(value)
    raw = re.sub(r"<br\s*/?>", " ", raw, flags=re.I)
    raw = re.sub(r"</(?:p|div|li)\s*>", " ", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", "", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def normalized(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def score_title(title, name):
    title_n, name_n = normalized(title), normalized(name)
    if not name_n:
        return 0
    if name_n in title_n:
        return 100 + len(name_n)
    words = [normalized(w) for w in re.findall(r"[A-Za-z0-9]+", name) if len(w) > 2]
    return sum(1 for word in words if word and word in title_n)


def commons_photo(place):
    name = place["name"]
    parts = [name, place.get("type", ""), place.get("address", "")]
    query = " ".join(part.strip() for part in parts if part and part.strip())[:220]
    params = {
        "action": "query", "format": "json", "formatversion": 2,
        "generator": "search", "gsrsearch": query, "gsrnamespace": 6,
        "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
        "iiurlwidth": 640,
    }
    data = get_json("https://commons.wikimedia.org/w/api.php", params)
    pages = data.get("query", {}).get("pages", [])
    candidates = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        mime = info.get("mime", "")
        thumb = info.get("thumburl") or info.get("url")
        if thumb and mime.startswith("image/") and mime not in {"image/svg+xml"}:
            candidates.append((score_title(page.get("title", ""), name), page, info))
    if not candidates:
        return None
    _, page, info = max(candidates, key=lambda item: item[0])
    meta = info.get("extmetadata", {})
    return {
        "url": info.get("thumburl") or info["url"],
        "source_url": info.get("descriptionurl", "https://commons.wikimedia.org/wiki/" + page.get("title", "").replace(" ", "_")),
        "source_title": page.get("title", "").removeprefix("File:"),
        "artist": clean_metadata(meta.get("Artist")) or clean_metadata(meta.get("Credit")),
        "license": clean_metadata(meta.get("LicenseShortName")),
        "license_url": clean_metadata(meta.get("LicenseUrl")),
        "mime": info.get("thumbmime") or info.get("mime", "image/jpeg"),
    }


def wikipedia_fallback(place):
    query = " ".join(p for p in [place["name"], place.get("address", "")] if p)[:220]
    params = {
        "action": "query", "format": "json", "formatversion": 2,
        "origin": "*", "generator": "search", "gsrsearch": query,
        "gsrnamespace": 0, "gsrlimit": 8, "prop": "pageimages|info",
        "piprop": "thumbnail", "pithumbsize": 640, "inprop": "url",
    }
    data = get_json("https://en.wikipedia.org/w/api.php", params)
    pages = [p for p in data.get("query", {}).get("pages", []) if p.get("thumbnail", {}).get("source")]
    if not pages:
        return None
    page = max(pages, key=lambda p: score_title(p.get("title", ""), place["name"]))
    return {
        "url": page["thumbnail"]["source"], "source_url": page.get("fullurl", "https://en.wikipedia.org/"),
        "source_title": page.get("title", "Wikipedia article"), "artist": "",
        "license": "See source page", "license_url": page.get("fullurl", ""),
        "mime": "image/jpeg",
    }


def extension_for(mime, url):
    clean_mime = (mime or "").split(";", 1)[0].lower()
    return mimetypes.guess_extension(clean_mime) or Path(url.split("?", 1)[0]).suffix or ".jpg"


def download_image(url, destination):
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=45) as response:
        content_type = response.headers.get("Content-Type", "image/jpeg").split(";", 1)[0].lower()
        if not content_type.startswith("image/"):
            raise ValueError(f"Unexpected content type: {content_type}")
        extension = extension_for(content_type, url)
        content = response.read(8 * 1024 * 1024 + 1)
        if len(content) > 8 * 1024 * 1024:
            raise ValueError("Thumbnail exceeded 8 MiB")
    destination = destination.with_suffix(extension)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def main():
    places = read_js_data(DATA_JS, "TRAVEL_PLACES")
    IMAGE_DIR.mkdir(exist_ok=True)
    try:
        manifest = read_js_data(PHOTO_JS, "TRAVEL_PHOTOS") if PHOTO_JS.exists() else {}
    except Exception:
        manifest = {}
    missing = []
    total = len(places)
    for index, place in enumerate(places, 1):
        name = place.get("name", "").strip()
        if not name:
            continue
        entry = manifest.get(name)
        if entry and (ROOT / entry.get("src", "")).is_file():
            continue
        photo = None
        error = ""
        for attempt in range(3):
            try:
                photo = commons_photo(place)
                if photo is None:
                    photo = wikipedia_fallback(place)
                break
            except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                error = str(exc)
                if attempt < 2:
                    time.sleep(5 * (attempt + 1))
        if photo:
            try:
                base = IMAGE_DIR / f"place-{index:04d}"
                local_path = download_image(photo["url"], base)
                manifest[name] = {
                    "src": local_path.relative_to(ROOT).as_posix(),
                    "sourceUrl": photo["source_url"], "sourceTitle": photo["source_title"],
                    "artist": photo["artist"], "license": photo["license"], "licenseUrl": photo["license_url"],
                }
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                missing.append((name, place.get("address", ""), f"download failed: {exc}"))
        else:
            missing.append((name, place.get("address", ""), error or "no usable wiki photo found"))
        if index % 20 == 0 or index == total:
            write_manifest(manifest)
            print(f"Processed {index}/{total}; saved {len(manifest)} photos; unavailable {len(missing)}", flush=True)
    write_manifest(manifest)
    with MISSING_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Address", "Reason"])
        writer.writerows(missing)
    print(f"Finished: {len(manifest)} local photos; {len(missing)} places without a photo.", flush=True)


if __name__ == "__main__":
    main()
