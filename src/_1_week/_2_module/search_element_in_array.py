def search(array: list[int], number: int) -> bool:
    small = 0
    big = len(array) - 1

    while small <= big:
        middle = small + (big - small) // 2
        if array[middle] == number:
            return True
        elif array[middle] > number:
            big = middle - 1
        else:
            small = middle + 1
    return False


if __name__ == "__main__":
    res1 = search([1, 2, 3, 4, 5, 6, 7, 8, 9], 5)
    print(res1)

    res2 = search([1, 2, 3, 4, 5, 6, 7, 8, 9], 10)
    print(res2)
