class FirstClass:
    def __init__(self) -> None:
        pass

    def first_class_first_method(self):
        pass


class SecondClass:
    def __init__(self) -> None:
        self.fc = FirstClass()

    def second_class_first_method(self):
        self.fc.first_class_first_method()


class ThirdClass:
    def __init__(self) -> None:
        pass

    def third_class_first_method(self):
        class ThirdClassNestedClass:
            def __init__(self) -> None:
                fc = FirstClass()
                fc.first_class_first_method()

                sc = SecondClass()
                sc.second_class_first_method()
