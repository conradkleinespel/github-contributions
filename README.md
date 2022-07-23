# Backup of Github contributions

This Python script helps keep a backup of open source contributions made on Github. This is useful if you want a log of all you've done even in the event a repository is deleted.

## How to use

Generate an [API token](https://github.com/settings/tokens/new) for the Github API without any scopes.

Create the Docker image for `monolith`:

```shell
git clone https://github.com/Y2Z/monolith.git
cd monolith
docker build -t monolith .
cd -
```

Run the script:

```shell
git clone git@github.com:conradkleinespel/github-contributions.git
cd github-contributions
pip install requests

TOKEN=github-token python main.py \
    -o path/to/output/dir \
    -c commits-list.txt \
    -i issues-list.txt \
    github-username
```

See the [backup of my own contributions](https://github.com/conradkleinespel/github-contributions-backup) for a more concrete example.
