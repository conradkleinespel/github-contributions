import datetime
import json
import requests
from subprocess import getstatusoutput
import os
import sys
from optparse import OptionParser

PER_PAGE = 100


def fetch_pulls(author, page=1):
    pulls = requests.get('https://api.github.com/search/issues', params={
        "q": f"author:{author} sort:created-asc is:pr is:merged is:public",
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
        if f"/repos/{author}/" not in item["repository_url"]  # exclude my own repositories
    ]

    if num_results < PER_PAGE:
        return pulls
    return pulls + fetch_pulls(page + 1)


def backup_pull(pull, output_dir):
    date = datetime.datetime.strptime(pull["created_at"], '%Y-%m-%dT%H:%M:%SZ')
    [_, _, _, organization, repo, _, pull_id] = pull['pull_request']['html_url'].split("/")
    pull_output_path = f"{date.year}-{date.month:02}-{date.day:02}-{organization}-{repo}-{pull_id}"

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


def get_html_page(url):
    (status, html_output) = getstatusoutput(
        f"docker run --rm monolith {url} -o - -s"
    )
    assert status == 0
    return html_output


def parse_args():
    parser = OptionParser(usage="usage: %prog [options] AUTHOR")
    parser.add_option("-o", "--output-dir", dest="output_dir",
                      help="Directory to write pull request content in", metavar="OUTPUT_DIR", default='./output')

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    author = args[0]

    return options, author


def main():
    (options, author) = parse_args()

    pulls = fetch_pulls(author)
    for pull in pulls:
        backup_pull(pull, options.output_dir)


if __name__ == '__main__':
    main()
