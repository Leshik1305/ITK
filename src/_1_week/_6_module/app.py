import asyncio
import json
import re
import ssl
import urllib.request

import uvicorn

URL = "https://api.exchangerate-api.com/v4/latest/"

CURRENCY_CODE_REGEX = re.compile(r"^[A-Z]{3}$")


def fetch_rates(base_currency: str):
    """Функция для получения курсов валют с API для указанной базовой валюты."""
    api_url = f"{URL}{base_currency}"

    try:
        # Создаем контекст SSL для безопасного HTTPS-соединения.
        context = ssl.create_default_context()

        # Открываем URL и читаем ответ
        # urllib.request.urlopen блокирует выполнение, пока не получит ответ.
        with urllib.request.urlopen(api_url, context=context) as response:
            status_code = response.status
            response_body_bytes = response.read()

            # Извлекаем Content-Type из заголовков ответа, по умолчанию 'application/json'
            content_type = response.headers.get("Content-Type", "application/json")

            return status_code, {"Content-Type": content_type}, response_body_bytes

    except Exception as e:
        print(f"Ошибка: {e}")
        return 500


async def asgi_application(scope, receive, send):
    """ASGI-приложение, которое проксирует курсы валют для выбранной базовой валюты."""
    # Убедимся, что это HTTP-запрос
    if scope["type"] != "http":
        return

    path = scope["path"]
    base_currency = path.strip("/").upper()

    final_status_code = 200
    final_headers_dict = {"Content-Type": "application/json"}
    final_response_body_bytes = b""

    # Проверяем, соответствует ли извлеченный код валюты ожидаемому формату
    if not base_currency or not CURRENCY_CODE_REGEX.match(base_currency):
        # Если валютный код недействителен, возвращаем 400 Bad Request
        final_status_code = 400
        error_message = json.dumps(
            {"error": "Неверный формат кода валюты в пути. "}
        ).encode("utf-8")
        final_response_body_bytes = error_message
    else:
        # Если код валюты валиден, запускаем блокирующую функцию получения данных в отдельном потоке.
        (
            final_status_code,
            final_headers_dict,
            final_response_body_bytes,
        ) = await asyncio.to_thread(fetch_rates, base_currency)

    # Преобразуем заголовки из словаря в список кортежей байтов,
    # как того требует спецификация ASGI (ключи в нижнем регистре).
    asgi_headers = [
        (k.lower().encode("ascii"), v.encode("ascii"))
        for k, v in final_headers_dict.items()
    ]
    # Обязательно добавляем заголовок Content-Length
    asgi_headers.append(
        (b"content-length", str(len(final_response_body_bytes)).encode("ascii"))
    )

    # Отправляем событие 'http.response.start' для начала HTTP-ответа
    await send(
        {
            "type": "http.response.start",
            "status": final_status_code,
            "headers": asgi_headers,
        }
    )

    # Отправляем событие 'http.response.body' с телом ответа
    await send(
        {
            "type": "http.response.body",
            "body": final_response_body_bytes,
            "more_body": False,  # Указываем, что это последний фрагмент тела ответа
        }
    )


if __name__ == "__main__":
    uvicorn.run("app:asgi_application", reload=True)

    # Пример правильный запросов: http://localhost:8000/usd    http://localhost:8000/EUR
    # Пример правильный запросов: http://localhost:8000/qwerty
