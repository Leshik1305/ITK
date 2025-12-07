import asyncio
import json

import aiohttp

REQUESTS_LIMIT = 5
TIMEOUT_SECONDS = 10  # Таймаут для каждого HTTP-запроса
MAX_JSON_SIZE_MB = (
    500  # Максимально допустимый размер JSON для попытки загрузки и парсинга
)
INPUT_URLS_FILE = "urls.txt"
RESULTS_FILE_PATH = "results.jsonl"


async def fetch_and_parse_url(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    url: str,
    timeout_seconds: int = TIMEOUT_SECONDS,
) -> tuple[str, dict | None]:
    """Функция асинхронного извлечения URL и парсинга JSON-ответов URL ввиде строки"""
    async with semaphore:
        try:
            async with session.get(url, timeout=timeout_seconds) as response:
                if response.status != 200:
                    # Проверка успешности HTTP-статуса
                    return url, None
                content_type = response.headers.get("Content-Type", "")
                # Проверка Content-Type на наличие JSON
                if (
                    "application/json" not in content_type
                    and "text/json" not in content_type
                ):
                    return url, None

                content_length = int(response.headers.get("Content-Length", "0"))
                # Проверка размера контента по заголовку Content-Length
                if content_length > MAX_JSON_SIZE_MB * 1024 * 1024:
                    return url, None

                try:
                    json_content = await response.json()
                    return url, json_content
                except aiohttp.ContentTypeError:
                    print(
                        f"Некорректный Content-Type для JSON из {url}. Невозможно распарсить JSON."
                    )
                    return url, None
                except json.JSONDecodeError as e:
                    print(f"Ошибка декодирования JSON из {url}: {e}")
                    return url, None
                except Exception as e:
                    print(f"Неожиданная ошибка {type(e).__name__} - {e}")
                    return url, None

        except aiohttp.ClientError as e:
            print(f"ClientError {type(e).__name__} - {e}")
            return url, None
        except asyncio.TimeoutError:
            print("Время ожидания ответа превышено")
            return url, None
        except Exception as e:
            print(f"Неожиданная ошибка {type(e).__name__} - {e}")
            return url, None


async def fetch_and_parse_urls(
    input_file_path: str,
    results_file_path: str,
) -> dict[str, dict]:
    """
    Функция асинхронного извлечения URL и парсинга JSON-ответов из файла с URL и записи их в файл
    """
    successful_results: dict[str, dict] = {}
    semaphore = asyncio.Semaphore(REQUESTS_LIMIT)
    try:
        output_file = open(results_file_path, "w", encoding="utf-8")
    except IOError as e:
        print(f"Невозможно открыть файл '{results_file_path}': {e}.")
        return {}

    try:
        async with aiohttp.ClientSession() as session:
            # Создаем одну HTTP-сессию aiohttp для всех запросов
            requests = []
            try:
                with open(input_file_path, "r", encoding="utf-8") as f_input:
                    for line in f_input:
                        url = line.strip()
                        if url:  # Пропускаем пустые строки
                            requests.append(
                                fetch_and_parse_url(session, semaphore, url)
                            )
            except IOError as e:
                print(f"Невозможно открыть файл '{input_file_path}': {e}.")
                return {}

            for future in asyncio.as_completed(requests):
                # Обрабатываем задачи по мере их завершения
                url, json_content = await future

                if json_content is not None:
                    successful_results[url] = json_content
                    try:
                        json_line = json.dumps(
                            {"url": url, "content": json_content}, ensure_ascii=False
                        )
                        output_file.write(json_line + "\n")
                        # output_file.flush() гарантирует, что данные будут записаны на диск после каждого успешного запроса.
                        output_file.flush()
                    except Exception as e:
                        print(
                            f"Ошибка при записи результата для URL '{url}' в файл: {e}"
                        )
    finally:
        output_file.close()

    return successful_results


if __name__ == "__main__":
    processed_results = asyncio.run(
        fetch_and_parse_url(INPUT_URLS_FILE, RESULTS_FILE_PATH)
    )
    print(processed_results)
