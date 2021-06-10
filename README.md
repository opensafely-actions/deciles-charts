# Deciles Chart Action

## Development

To set up a development environment, execute:

```sh
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -r requirements.dev.txt
```

For QA, execute:

```sh
bin/codestyle.sh .
bin/mypy.sh .
```

Use [pip-tools][] to manage dependencies.
For example, to keep the development environment in sync, execute:

```sh
pip-sync requirements.txt requirements.dev.txt
```

[pip-tools]: https://github.com/jazzband/pip-tools/
