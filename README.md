# Backup of Github contributions

This Python script helps keep a backup of open source contributions made on Github. This is useful if you want a log of all you've done even in the event a repository is deleted.

## How to use

Generate an [API token](https://github.com/settings/tokens) for the Github API without any scopes.

Run the script:

```shell
git clone git@github.com:conradkleinespel/github-contributions.git
cd github-contributions
docker build -t monolith .

pip install requests # or install via system package manager

TOKEN=github-token python main.py \
    -o ../github-contributions-backup/ \
    -c ../github-contributions-backup/commits.txt \
    -i ../github-contributions-backup/issues.txt \
    -s 2023-11-15 \
    conradkleinespel
```

Only pull requests after the date in the `-s` option are downloaded. This helps with updating the backup regularly.

See the [backup of my own contributions](https://github.com/conradkleinespel/github-contributions-backup) for a more concrete example.
