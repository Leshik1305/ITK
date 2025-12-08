import csv
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, Process, Queue

N = 1000000
csv_filename = "results.csv"


def generate_data(n):
    """Генерирует список из n случайных целых чисел в диапазоне от 1 до 1000."""
    data = [random.randint(1, 1000) for _ in range(n)]
    return data


def is_prime(num):
    """Проверяет, является ли число простым перебором (чтобы усложнить функцию)."""
    if num < 2:
        return False
    if num == 2:
        return True
    for i in range(2, num - 1):
        if num % i == 0:
            return False
    return True


def benchmark_task(func, data_to_process, method_name, results_list):
    """
    Запускает заданную функцию для обработки данных и измеряет время выполнения.
    """
    print(f"\nЗапуск '{method_name}'...")
    start_time = time.perf_counter()
    func(data_to_process)
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"'{method_name}' завершен за {duration:.4f} секунд.")
    results_list.append({"Метод": method_name, "Время (секунды)": f"{duration}сек."})


# Вариант А: Использование пула потоков с concurrent.futures
def thread_pool(data):
    """Используем пул потоков (ThreadPoolExecutor)."""
    max_workers = os.cpu_count() or 4
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        result = list(executor.map(is_prime, data))
        return result


# Вариант Б: Использование multiprocessing.Pool с пулом процессов
def multiprocess_pool(data):
    """Используем пул процессов (multiprocessing.Pool)."""
    num_processes = os.cpu_count() or 4
    with Pool(processes=num_processes) as pool:
        result = list(pool.map(is_prime, data))
        return result


# Вариант В: Создание отдельных процессов с использованием multiprocessing.Process и очередей (multiprocessing.Queue)
def worker_process(task_queue, result_queue):
    """
    Функция рабочего процесса: берет числа из очереди задач,
    обрабатывает их и помещает результаты в очередь результатов.
    """
    while True:
        task = task_queue.get()
        if task is None:
            break
        result = is_prime(task)
        result_queue.put(result)
    result_queue.put(None)


def individual_processes_with_queues(data):
    """Обработка данных с использованием отдельных процессов и очередей."""
    num_processes = os.cpu_count() or 4
    task_queue = Queue()
    result_queue = Queue()

    for num in data:
        task_queue.put(num)

    processes = []
    for _ in range(num_processes):
        p = Process(target=worker_process, args=(task_queue, result_queue))
        processes.append(p)
        p.start()

    for _ in range(num_processes):
        task_queue.put(None)

    finished_workers = 0

    while finished_workers < num_processes:
        res = result_queue.get()
        if res is None:
            finished_workers += 1

    for p in processes:
        p.join()


def single_threaded(data):
    """Последовательная обработка списка чисел."""
    result = [is_prime(num) for num in data]
    return result


if __name__ == "__main__":
    benchmark_results = []

    # Вариант А: Пул потоков
    benchmark_task(
        thread_pool,
        generate_data(N),
        "Пул потоков (concurrent.futures)",
        benchmark_results,
    )

    # Вариант Б: Пул процессов
    benchmark_task(
        multiprocess_pool,
        generate_data(N),
        "Пул процессов (multiprocessing.Pool)",
        benchmark_results,
    )

    # Вариант В: Отдельные процессы + Очереди
    benchmark_task(
        individual_processes_with_queues,
        generate_data(N),
        "Отдельные процессы + Очереди",
        benchmark_results,
    )

    # Последовательный вариант
    benchmark_task(
        single_threaded,
        generate_data(N),
        "Последовательная обработка",
        benchmark_results,
    )

    csv_filename = "results.csv"

    fieldnames = ["Метод", "Время (секунды)"]

    try:
        with open(csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for row in benchmark_results:
                writer.writerow(row)

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
