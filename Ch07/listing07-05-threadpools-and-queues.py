from concurrent.futures import ThreadPoolExecutor
import queue
import requests
import textwrap


def print_column(text, column):
    wrapped = textwrap.fill(text, 45)
    indent_level = 50 * column
    indented = textwrap.indent(wrapped, " " * indent_level)
    print(indented)


def fetch(urls, responses, parsed):
    while True:
        url = urls.get()
        if url is None:
            print_column("Got instruction to finish", 0)
            return
        print_column(f"Getting {url}", 0)
        response = requests.get(url)
        print_column(f"Storing {response} from {url}", 0)
        responses.put(response)
        urls.task_done()


def parse(urls, responses, parsed):
    # Wait for the initial URLs to be processed
    print_column("Waiting for url fetch thread", 1)
    urls.join()

    while not responses.empty():
        response = responses.get()
        print_column(f"Starting processing of {response}", 1)

        if response.ok:
            data = response.json()
            for commit in data:
                parsed.put(commit)

            links = response.headers["link"].split(",")
            for link in links:
                if "next" in link:
                    url = link.split(";")[0].strip("<>")
                    print_column(f"Discovered new url: {url}", 1)
                    urls.put(url)

        responses.task_done()
        if responses.empty():
            # We have no responses left, so the loop will
            # end. Wait for all queued urls to be fetched
            # before continuing
            print_column("Waiting for url fetch thread", 1)
            urls.join()

    # We reach this point if there are no responses to process
    # after waiting for the fetch thread to catch up. Tell the
    # fetch thread that it can stop now, then exit this thread.
    print_column("Sending instruction to finish", 1)
    urls.put(None)


def get_commit_info(repos):
    urls = queue.Queue()
    responses = queue.Queue()
    parsed = queue.Queue()

    for (username, repo) in repos:
        urls.put(f"https://api.github.com/repos/{username}/{repo}/commits")

    with ThreadPoolExecutor() as pool:
        fetcher = pool.submit(fetch, urls, responses, parsed)
        parser = pool.submit(parse, urls, responses, parsed)
    print(f"{parsed.qsize()} commits found")


if __name__ == "__main__":
    get_commit_info(
        [("MatthewWilkes", "apd.sensors"), ("MatthewWilkes", "apd.aggregation")]
    )
