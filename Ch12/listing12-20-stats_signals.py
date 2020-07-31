import signal
def stats_signal_handler(sig, frame, data_processors=None):
    for data_processor in data_processors:
        click.echo(
            click.style(data_processor.name, bold=True, fg="red") + " " + data_processor.stats()
        )
    return

signal_handler = functools.partial(stats_signal_handler, data_processors=handlers)
signal.signal(signal.SIGINFO, signal_handler)

