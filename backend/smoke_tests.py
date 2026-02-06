import os
import sys
import httpx


BASE_URL = os.getenv("BEE_BASE_URL", "http://localhost:8080")


def _print(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def check_health() -> bool:
    try:
        resp = httpx.get(f"{BASE_URL}/api/health", timeout=10)
        ok = resp.status_code == 200
        _print("health", ok, f"status={resp.status_code}")
        return ok
    except Exception as exc:
        _print("health", False, str(exc))
        return False


def check_web_search() -> bool:
    if not os.getenv("BRAVE_SEARCH_API_KEY"):
        _print("web search", True, "skipped (BRAVE_SEARCH_API_KEY not set)")
        return True
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/web/search",
            json={"query": "B.E.E. agent platform"},
            timeout=20,
        )
        data = resp.json()
        ok = resp.status_code == 200 and isinstance(data.get("results"), list)
        _print("web search", ok, f"results={len(data.get('results', []))}")
        return ok
    except Exception as exc:
        _print("web search", False, str(exc))
        return False


def check_youtube_transcribe() -> bool:
    if not os.getenv("OPENAI_API_KEY"):
        _print("youtube transcribe", True, "skipped (OPENAI_API_KEY not set)")
        return True
    video = os.getenv("BEE_YOUTUBE_TEST")
    if not video:
        _print("youtube transcribe", True, "skipped (BEE_YOUTUBE_TEST not set)")
        return True
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/youtube/transcribe",
            json={"video": video, "store_memory": False},
            timeout=120,
        )
        data = resp.json()
        ok = resp.status_code == 200 and data.get("ok") is True and bool(data.get("text"))
        _print("youtube transcribe", ok, f"title={data.get('title')}")
        return ok
    except Exception as exc:
        _print("youtube transcribe", False, str(exc))
        return False


def check_browser_use() -> bool:
    if not os.getenv("BROWSER_USE_API_KEY"):
        _print("browser-use", True, "skipped (BROWSER_USE_API_KEY not set)")
        return True
    url = os.getenv("BEE_BROWSER_USE_URL")
    if not url:
        _print("browser-use", True, "skipped (BEE_BROWSER_USE_URL not set)")
        return True
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/browser-use/extract",
            json={"url": url, "store_memory": False},
            timeout=120,
        )
        data = resp.json()
        ok = resp.status_code == 200 and data.get("ok") is True
        _print("browser-use", ok, f"status={data.get('status')}")
        return ok
    except Exception as exc:
        _print("browser-use", False, str(exc))
        return False


def main() -> int:
    checks = [
        check_health(),
        check_web_search(),
        check_youtube_transcribe(),
        check_browser_use(),
    ]
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
