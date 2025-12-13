import datetime


class CreatedAtMeta(type):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.created_at = datetime.datetime.now()


class MyClass(metaclass=CreatedAtMeta):
    pass

class CreatedAtMeta1(type):
    def __new__(cls, name, bases, attrs):
        instance = super().__new__(cls, name, bases, attrs)
        current_time = datetime.datetime.now()
        setattr(instance, 'created_at', current_time)
        return instance

class MyClass1(metaclass=CreatedAtMeta1):
    pass


if __name__ == "__main__":
    a = MyClass()
    print(a.created_at)

    b= MyClass1()
    print(b.created_at)
