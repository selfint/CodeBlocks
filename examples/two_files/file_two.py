from file_one import FirstClass


class SecondClass:
    def __init__(self):
        pass

    def second_class_second_method(self):
        pass


if __name__ == "__main__":
    fc = FirstClass()
    fc.first_class_first_method()

    sc = SecondClass()
    sc.second_class_second_method()
