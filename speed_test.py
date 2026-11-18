#!/usr/bin/env python3
"""Measure download speed from a URL using ten sequential GET requests."""

import argparse
import sys
from http.client import HTTPException
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import urlopen


REQUEST_COUNT = 10
CHUNK_SIZE = 64 * 1024
TIMEOUT_SECONDS = 30


def measure_download(url):
    started_at = perf_counter()
    downloaded_bytes = 0
    with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        content_length = response.headers.get("Content-Length")
        is_chunked = response.headers.get("Transfer-Encoding", "").lower() == "chunked"
        while chunk := response.read(CHUNK_SIZE):
            downloaded_bytes += len(chunk)
        if content_length is not None and not is_chunked:
            if downloaded_bytes != int(content_length):
                raise HTTPException(
                    f"неполный ответ: получено {downloaded_bytes} из {content_length} байт"
                )

    return perf_counter() - started_at, downloaded_bytes


def main():
    parser = argparse.ArgumentParser(description="Измерить скорость скачивания по URL.")
    parser.add_argument("url", help="адрес ресурса по HTTP или HTTPS")
    args = parser.parse_args()

    try:
        url = urlsplit(args.url)
        valid_url = url.scheme in ("http", "https") and url.hostname
    except ValueError:
        valid_url = False
    if not valid_url:
        parser.error("укажите полный URL, начинающийся с http:// или https://")

    total_seconds = 0.0
    total_bytes = 0
    for request_number in range(1, REQUEST_COUNT + 1):
        try:
            seconds, downloaded_bytes = measure_download(args.url)
        except (OSError, HTTPException, ValueError) as error:
            print(f"Ошибка запроса {request_number}/{REQUEST_COUNT}: {error}", file=sys.stderr)
            return 1
        total_seconds += seconds
        total_bytes += downloaded_bytes

    average_seconds = total_seconds / REQUEST_COUNT
    speed_mbps = total_bytes * 8 / total_seconds / 1_000_000
    print(f"Среднее время запроса: {average_seconds:.3f} с")
    print(f"Общий объём скачанных данных: {total_bytes} байт")
    print(f"Скорость скачивания: {speed_mbps:.3f} Мбит/с")
    return 0


if __name__ == "__main__":
    sys.exit(main())
