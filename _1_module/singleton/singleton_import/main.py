from my_singleton import single

single_1 = single
single_2 = single
if __name__ == "__main__":
    print(single_1 is single_2)
