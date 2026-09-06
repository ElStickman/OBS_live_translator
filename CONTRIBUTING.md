# Contributing

Thank you for helping improve the project.

## Before opening a change

- Search existing issues and discussions.
- Use an issue for bugs or substantial feature proposals.
- Do not include recordings, names, tokens, device identifiers, or other private
  information in reports.
- Keep changes focused and avoid unrelated formatting rewrites.

## Development setup

Follow the first-time setup in `README.md`, activate the virtual environment,
and install `requirements-nvidia.txt`. CUDA is not required to run unit tests.

Run the test suite before submitting a pull request:

```powershell
python -m unittest discover -s tests -v
```

## Pull requests

- Explain the problem and the behavior of the solution.
- Include or update tests when behavior changes.
- Update documentation for user-facing changes.
- Confirm that you have the right to contribute the submitted code and assets.
- By contributing, you agree that your contribution is licensed under the MIT
  license used by this repository.

Maintainers may request changes or decline contributions that do not fit the
project's scope or maintenance capacity.
