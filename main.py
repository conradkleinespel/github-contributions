import requests
from subprocess import getstatusoutput
import os

PER_PAGE = 100
AUTHOR = os.environ.get("AUTHOR")


def fetch_pulls(page=1):
    pulls = requests.get('https://api.github.com/search/issues', params={
        "q": f"author:{AUTHOR} sort:created-asc is:pr is:merged",
        "page": page,
        "per_page": PER_PAGE,
    }, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {os.environ.get('TOKEN')}",
    })
    pulls.raise_for_status()
    pulls = pulls.json()

    num_results = len(pulls['items'])
    pulls = [
        item for item in pulls["items"]
        if f"/repos/{AUTHOR}/" not in item["repository_url"]  # exclude my own repositories
    ]

    if num_results < PER_PAGE:
        return pulls
    return pulls + fetch_pulls(page + 1)


def get_html_page(url):
    (status, html_output) = getstatusoutput(
        f"docker run --rm monolith {url} -o - -s"
    )
    assert status == 0
    return html_output


def main():
    output_dir = os.environ.get('OUTPUT_DIR', '.')
    pulls = fetch_pulls()

    for pull in pulls:
        [_, _, _, organization, repo, _, pull_id] = pull['pull_request']['html_url'].split("/")
        pull_output_path = f"{organization}-{repo}-{pull_id}"

        with \
                open(f"{output_dir}/{pull_output_path}-conversation.html", "w") as html_conversation_file, \
                open(f"{output_dir}/{pull_output_path}-commits.html", "w") as html_commits_file, \
                open(f"{output_dir}/{pull_output_path}-files.html", "w") as html_files_file, \
                open(f"{output_dir}/{pull_output_path}.diff", "w") as diff_file, \
                open(f"{output_dir}/{pull_output_path}.patch", "w") as patch_file:
            html_conversation_file.write(get_html_page(pull['pull_request']['html_url']))
            html_commits_file.write(get_html_page(f"{pull['pull_request']['html_url']}/commits"))
            html_files_file.write(get_html_page(f"{pull['pull_request']['html_url']}/files"))
            diff_file.write(requests.get(pull['pull_request']['diff_url'], allow_redirects=True).text)
            patch_file.write(requests.get(pull['pull_request']['patch_url'], allow_redirects=True).text)


if __name__ == '__main__':
    main()
