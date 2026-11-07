#!/usr/bin/env python3
"""Fetch five verified public-domain USGS illustrations/photos for offline KALE.

Run while online once: python3 tools/install_open_images.py
No external dependency. Images remain on the device for offline operation.
A failed download does not remove the built-in KALE SVG diagrams.
"""
from __future__ import annotations

import os
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "web" / "assets" / "public-domain"
MAX_BYTES = 5 * 1024 * 1024
SOURCES = (
    ("drop-cover-holdon.png",
     "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/Drop-Cover-HoldOn.png",
     "png"),
    ("earthquake-damage.jpg",
     "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/earthquake-damage_0.jpg",
     "jpg"),
    ("landslide.jpg",
     "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/landslide.jpg",
     "jpg"),
    ("drinking-water.jpg",
     "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/thumbnails/image/P8150428.JPG",
     "jpg"),
    ("flooded-road.jpg",
     "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/IMG_1451.JPG",
     "jpg"),
)


def valid_image(path: Path, image_format: str) -> bool:
    if not path.is_file() or not (1024 < path.stat().st_size <= MAX_BYTES):
        return False
    with path.open("rb") as handle:
        header = handle.read(12)
    if image_format == "png":
        return header.startswith(b"\\x89PNG\\r\\n\\x1a\\n")
    return header.startswith(b"\\xff\\xd8\\xff")


def download(name: str, url: str, image_format: str) -> None:
    target = DEST / name
    if valid_image(target, image_format):
        print(f"OK: {name} zaten yerelde.")
        return
    DEST.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "KALE-offline-visuals/1.0", "Accept": "image/*"},
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        length = response.headers.get("Content-Length", "")
        if length.isdecimal() and int(length) > MAX_BYTES:
            raise ValueError("Görsel 5 MiB üstünde.")
        with tempfile.NamedTemporaryFile(
            prefix=".kale-photo-", dir=DEST, delete=False
        ) as tmp:
            pending = Path(tmp.name)
            try:
                total = 0
                while True:
                    chunk = response.read(min(65536, MAX_BYTES + 1 - total))
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("Görsel boyut limiti aşıldı.")
                    tmp.write(chunk)
                tmp.flush()
                os.fsync(tmp.fileno())
            except BaseException:
                pending.unlink(missing_ok=True)
                raise
    if not valid_image(pending, image_format):
        pending.unlink(missing_ok=True)
        raise ValueError("Görsel imzası veya boyutu geçersiz.")
    pending.replace(target)
    print(f"OK: {name} yerel olarak kaydedildi ({total // 1024} KiB).")


def main() -> int:
    failed = 0
    for name, url, image_format in SOURCES:
        try:
            download(name, url, image_format)
        except Exception as exc:
            print(f"UYARI: {name} indirilemedi: {exc}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"{failed} görsel yok. Saha ekranında özgün çevrimdışı SVG şemalar kullanılacak.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
