import datetime
import requests
from subprocess import getstatusoutput
import os
import sys
from optparse import OptionParser
import logging

PER_PAGE = 100


def fetch_pulls(author, since=None, page=1):
    pulls = requests.get('https://api.github.com/search/issues', params={
        "q": f"author:{author} sort:created-asc is:pr is:merged is:public" + (f" created:>={since}" if since else ""),
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

    logging.info(f"Fetching pull request: {date} - {organization}/{repo}/{pull_id}")

    with \
            open(f"{output_dir}/pull-requests/{pull_output_path}-conversation.html", "w") as html_conversation_file, \
            open(f"{output_dir}/pull-requests/{pull_output_path}-commits.html", "w") as html_commits_file, \
            open(f"{output_dir}/pull-requests/{pull_output_path}-files.html", "w") as html_files_file, \
            open(f"{output_dir}/pull-requests/{pull_output_path}.diff", "w") as diff_file, \
            open(f"{output_dir}/pull-requests/{pull_output_path}.patch", "w") as patch_file:
        html_conversation_file.write(get_html_page(pull['pull_request']['html_url']))
        html_commits_file.write(get_html_page(f"{pull['pull_request']['html_url']}/commits"))
        html_files_file.write(get_html_page(f"{pull['pull_request']['html_url']}/files"))
        diff_file.write(requests.get(pull['pull_request']['diff_url'], allow_redirects=True).text)
        patch_file.write(requests.get(pull['pull_request']['patch_url'], allow_redirects=True).text)


def backup_issue(issue_date, issue_url, output_dir):
    [_, _, _, organization, repo, _, issue_id] = issue_url.split("/")
    issue_output_path = f"{issue_date}-{organization}-{repo}-{issue_id}"

    logging.info(f"Fetching issue: {issue_date} - {organization}/{repo}/{issue_id}")

    with open(f"{output_dir}/issues/{issue_output_path}.html", "w") as html_files_file:
        html_files_file.write(get_html_page(f"{issue_url}"))


def backup_commit(commit_date, commit_url, output_dir):
    [_, _, _, organization, repo, _, commit_hash] = commit_url.split("/")
    commit_output_path = f"{commit_date}-{organization}-{repo}-{commit_hash}"

    logging.info(f"Fetching commit: {commit_date} - {organization}/{repo}/{commit_hash}")

    with \
            open(f"{output_dir}/commits/{commit_output_path}-files.html", "w") as html_files_file, \
            open(f"{output_dir}/commits/{commit_output_path}.diff", "w") as diff_file, \
            open(f"{output_dir}/commits/{commit_output_path}.patch", "w") as patch_file:
        html_files_file.write(get_html_page(f"{commit_url}"))
        diff_file.write(requests.get(f"{commit_url}.diff", allow_redirects=True).text)
        patch_file.write(requests.get(f"{commit_url}.patch", allow_redirects=True).text)


def get_html_page(url):
    (status, html_output) = getstatusoutput(
        f"docker run --rm monolith {url} -o - -s"
    )
    assert status == 0
    return html_output


def create_directory(path):
    if not os.path.isdir(path):
        os.mkdir(path)


def parse_args():
    parser = OptionParser(usage="usage: %prog [options] AUTHOR")
    parser.add_option(
        "-o",
        dest="output_dir",
        help="Directory to write pull request content in",
        metavar="OUTPUT_DIR",
        default='./output',
    )
    parser.add_option(
        "-c",
        dest="commits_listing",
        help="File in which to list additional commits to backup",
        metavar="COMMITS_LISTING",
    )
    parser.add_option(
        "-i",
        dest="issues_listing",
        help="File in which to list additional issues to backup",
        metavar="ISSUES_LISTING",
    )
    parser.add_option(
        "-s",
        dest="since",
        help="Only search pull requests created since date (yyyy-mm-dd)",
        metavar="SINCE_DATE",
    )

    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    author = args[0]

    return options, author


def main():
    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    (options, author) = parse_args()

    create_directory(f"{options.output_dir}/pull-requests")
    create_directory(f"{options.output_dir}/issues")
    create_directory(f"{options.output_dir}/commits")

    pulls = fetch_pulls(author, options.since)
    for pull in pulls:
        backup_pull(pull, options.output_dir)

    if options.commits_listing:
        with open(options.commits_listing, 'r') as commits_listing:
            commits = [commit for commit in commits_listing.read().split('\n') if commit]
            for [commit_date, commit_url] in [commit.split(' ') for commit in commits]:
                backup_commit(commit_date, commit_url, options.output_dir)

    if options.issues_listing:
        with open(options.issues_listing, 'r') as issues_listing:
            issues = [issue for issue in issues_listing.read().split('\n') if issue]
            for [issue_date, issue_url] in [issue.split(' ') for issue in issues]:
                backup_issue(issue_date, issue_url, options.output_dir)


if __name__ == '__main__':
    main()
