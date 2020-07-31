import typing as t

def add_number_from_callback(a: t.Callable[[], int], b: t.Callable[[], int]) -> int:
    return a() + b()

def constant() -> int:
    return 5

print(add_number_from_callback(constant, constant))

