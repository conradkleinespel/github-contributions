# Saving Github contributions

This Python script helps keep a backup of open source contributions made on Github.


To run it, generate an API token for the Github API. Then follow these steps.

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
TOKEN=github-token python main.py -o path/to/output/dir github-username
```