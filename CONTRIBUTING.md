# Contributing to Doral Courts CLI

Thank you for your interest in contributing to the Doral Courts CLI project!

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`uv run python -m pytest test_html_extractor.py -v`)
6. Commit your changes (`git commit -m 'Add some amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yorch/doral-courts.git

# Install dependencies
uv sync

# Run tests
uv run python -m pytest test_html_extractor.py -v
```

## Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

## Testing

- Add tests for new functionality
- Ensure all existing tests continue to pass
- Test both happy path and edge cases

## Pull Request Process

1. Update the documentation if needed
2. Add tests for your changes
3. Ensure your code follows the existing style
4. Update the README.md if you add new commands or features
5. Your PR will be reviewed and merged if approved

## Questions?

Feel free to open an issue if you have questions about contributing!
