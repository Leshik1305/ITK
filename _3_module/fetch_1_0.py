import asyncio
import json

from aiohttp import ClientError, ClientSession

TIMEOUT_SECONDS = 5
ERROR_STATUS = 0
ERROR_TIMEOUT_STATUS = 408
CLIENT_ERROR_STATUS = 400
REQUESTS_LIMIT = 5
FILE_PATH = "./results.jsonl"


async def fetch_url(
    session: ClientSession,
    semaphore: asyncio.Semaphore,
    url: str,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> tuple[str, int]:
    """Функция асинхронного извлечения URL и статуса ответа из одного запроса"""
    async with semaphore:
        try:
            async with session.get(url, timeout=timeout_seconds) as response:
                return url, response.status
        except TimeoutError:
            # Обработка ошибок таймаута.
            return url, ERROR_TIMEOUT_STATUS

        except ClientError:
            # Обработка клиентских ошибок.
            return url, CLIENT_ERROR_STATUS

        except Exception:
            # Обработка прочих ошибок.

            return url, ERROR_STATUS


async def fetch_urls(urls: list[str], file_path: str) -> dict[str, int]:
    """Функция асинхронного извлечения URL и статуса ответа из списка запросов и записи их в файл"""
    dict_results: dict[str, int] = {}
    semaphore = asyncio.Semaphore(REQUESTS_LIMIT)

    async with ClientSession() as session:
        requests = [fetch_url(session, semaphore, url) for url in urls]

        result = await asyncio.gather(*requests)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for url, status_code in result:
                dict_results[url] = status_code
                line = json.dumps(
                    {"url": url, "status_code": status_code}, ensure_ascii=False
                )
                f.write(line + "\n")
    except Exception as e:
        return f"Ошибка: {e}"
    return dict_results


if __name__ == "__main__":
    urls = [
        "https://example.com",
        "https://httpbin.org/status/404",
        "https://nonexistent.url",
    ]

    res = asyncio.run(fetch_urls(urls, FILE_PATH))
    print(res)
