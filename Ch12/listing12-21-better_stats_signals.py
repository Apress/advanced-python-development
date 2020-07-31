def stats_signal_handler(sig, frame, original_sigint_handler=None, data_processors=None):
    for data_processor in data_processors:
        click.echo(
            click.style(data_processor.name, bold=True, fg="red") + " " + data_processor.stats()
        )
    if sig == signal.SIGINT:
        click.secho("Press Ctrl+C again to end the process", bold=True)
        handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, original_sigint_handler)
        asyncio.get_running_loop().call_later(5, install_ctrl_c_signal_handler, handler)
    return


def install_ctrl_c_signal_handler(signal_handler):
    click.secho("Press Ctrl+C to view statistics", bold=True)
    signal.signal(signal.SIGINT, signal_handler)


def install_signal_handlers(running_data_processors):
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    signal_handler = functools.partial(
        stats_signal_handler,
        data_processors=running_data_processors,
        original_sigint_handler=original_sigint_handler,
    )

    for signal_name in "SIGINFO", "SIGUSR1", "SIGINT":
        try:
            signal.signal(signal.Signals[signal_name], signal_handler)
        except KeyError:
            pass

