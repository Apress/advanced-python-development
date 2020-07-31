class ExampleDescriptor:

    def __set_name__(self, instance, name):
        self.name = name

    def __get__(self, instance, owner):
        print(f"{self}.__get__({instance}, {owner})")
        if not instance:
            # We were called on the class available as `owner`
            return self
        else:
            # We were called on the instance called `instance`
            if self.name in instance.__dict__:
                return instance.__dict__[self.name]
            else:
                raise AttributeError(self.name)

    def __set__(self, instance, value):
        print(f"{self}.__set__({instance}, {value})")
        instance.__dict__[self.name] = value

    def __delete__(self, instance):
        print(f"{self}.__delete__({instance}")
        del instance.__dict__[self.name]

class A:
    foo = ExampleDescriptor()
