# Contributing

See [GUIDELINES.md](GUIDELINES.md) for coding conventions and [DESIGN.md](DESIGN.md) for architecture.

## Dev setup

```bash
git clone https://github.com/<<AUTHOR_NAME>>/<<PROJECT_NAME>>.git
cd <<PROJECT_NAME>>
make install
make test
```

## Pull requests

- Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- Branch naming: `<type>/<short-description>`
- CI must pass; tests included
- One change → one CHANGELOG line under `[Unreleased]`
