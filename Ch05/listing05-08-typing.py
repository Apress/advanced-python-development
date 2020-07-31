import functools
import random
import typing as t

ViewFuncReturn = t.TypeVar("ViewFuncReturn")
ErrorReturn = int

def result_or_number(
    func: t.Callable[[], ViewFuncReturn]
) -> t.Callable[[], t.Union[ViewFuncReturn, ErrorReturn]]:
    @functools.wraps(func)
    def wrapped() -> t.Union[ViewFuncReturn, ErrorReturn]:

        pass_through = random.choice([True, False])
        if pass_through:
            return func()
        else:
            return random.randint(0, 100)

    return wrapped

@result_or_number
def hello() -> str:
    return "Hello!"

@result_or_number
def three() -> int:
    return 3

if t.TYPE_CHECKING:
    reveal_type(hello)
else:
    print(hello())
