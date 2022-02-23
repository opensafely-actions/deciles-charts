# Notes for developers

## System requirements

### `just`

[`just`][1] is a handy way to save and run project-specific commands.
It's unrelated to the package with the same name on PyPI.

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Show all available commands
just # Shortcut for just --list
```

## Development

Set up a local development environment with:

```sh
just devenv
```

## Tests

Run the tests with:

```sh
just test
```

[1]: https://github.com/casey/just/
