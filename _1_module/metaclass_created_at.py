import datetime


class CreatedAtMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.created_at = datetime.datetime.now()


class MyClass(metaclass=CreatedAtMeta):
    pass


if __name__ == "__main__":
    a = MyClass()
    print(a.created_at)
