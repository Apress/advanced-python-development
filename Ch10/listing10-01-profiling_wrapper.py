_Coroutine_Result = t.TypeVar("_Coroutine_Result")

def wrap_coroutine(
    f: t.Callable[..., t.Coroutine[t.Any, t.Any, _Coroutine_Result]], debug: bool=False,
) -> t.Callable[..., _Coroutine_Result]:
    """Given a coroutine, return a function that runs that coroutine
    in a new event loop in an isolated thread"""

    @functools.wraps(f)
    def run_in_thread(*args: t.Any, **kwargs: t.Any) -> _Coroutine_Result:
        loop = asyncio.new_event_loop()
        wrapped = f(*args, **kwargs)
        
        if debug:
            # Create a new function that runs the loop inside a cProfile
            # session, so it can be profiled transparently

            def fn():
                import cProfile

                return cProfile.runctx(
                    "loop.run_until_complete(wrapped)",
                    {},
                    {"loop": loop, "wrapped": wrapped},
                    sort="cumulative",
                )

            task_callable = fn
        else:
            # If not debugging just submit the loop run function with the desired 
            # coroutine
            task_callable = functools.partial(loop.run_until_complete, wrapped)
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(task_callable)
        # Mypy can get confused when nesting generic functions, like we do here
        # The fact that Task is generic means we lose the association with
        # _CoroutineResult. Adding an explicit cast restores this.
        return t.cast(_Coroutine_Result, task.result())

    return run_in_thread


def interactable_plot_multiple_charts(
    *args: t.Any, debug: bool=False, **kwargs: t.Any
) -> t.Callable[..., Figure]:
    with_config = functools.partial(plot_multiple_charts, *args, **kwargs)
    return wrap_coroutine(with_config, debug=debug)

