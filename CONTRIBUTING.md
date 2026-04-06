# Contributing to PDF Splitter

Thanks for your interest in contributing! This project is small and welcoming — issues, ideas, and pull requests are all appreciated.

## Ways to contribute

- 🐛 **Report bugs** — open an issue with steps to reproduce, the PDF type/size if relevant, and your Python version.
- 💡 **Suggest features** — open an issue describing the use case before writing code, especially for larger changes.
- 📖 **Improve docs** — README fixes, typos, clearer instructions are always welcome.
- 🧑‍💻 **Submit code** — bug fixes, new features, or refactors via pull request.

## Development setup

1. **Fork** the repo on GitHub.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/pdf-splitter.git
   cd pdf-splitter
   ```
3. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Run the app:**
   ```bash
   python app.py
   ```
   Open <http://localhost:5000> in your browser.

## Making a change

1. **Create a branch** from `master`:
   ```bash
   git checkout -b feature/short-description
   ```
   Use `fix/...` for bug fixes, `docs/...` for documentation, `feature/...` for new features.

2. **Keep changes focused** — one logical change per PR. Smaller PRs get reviewed faster.

3. **Test manually** before pushing:
   - Upload a small PDF (1-10 pages)
   - Upload a large PDF (100+ pages)
   - Try downloading the ZIP and individual pages
   - Try an invalid file (e.g., a `.txt`) to confirm error handling

4. **Commit** with a clear message:
   ```bash
   git commit -m "Fix: handle PDFs with encrypted pages"
   ```
   Prefixes: `Add:`, `Fix:`, `Update:`, `Remove:`, `Docs:`, `Refactor:`.

5. **Push** to your fork and **open a Pull Request** against `master`.

## Pull request guidelines

Your PR description should include:

- **What** the change does
- **Why** it's needed (link to an issue if there is one)
- **How** you tested it
- **Screenshots/GIFs** for any UI changes

## Code style

- **Python:** follow [PEP 8](https://peps.python.org/pep-0008/). Keep functions small and focused.
- **HTML/CSS/JS** in `templates/`: keep it dependency-free where possible — this app deliberately avoids a heavy frontend stack.
- **No new dependencies** without discussing in an issue first. Every dependency is a maintenance cost.
- **No tracking, analytics, or telemetry** in the core app. Privacy is the point.

## What we're looking for

Good fits for this project:

- Performance improvements for large PDFs
- Better error messages for malformed/encrypted PDFs
- Accessibility improvements
- Bug fixes
- Translations

Probably **not** a fit (open an issue to discuss first):

- Heavy frameworks (React, Vue, etc.) on the frontend
- Server-side persistence / databases
- User accounts or authentication
- Telemetry or analytics

## Reporting security issues

If you find a security vulnerability, **please do not open a public issue.** Instead, email the maintainer directly or use GitHub's private security advisory feature.

## Code of conduct

Be kind, be patient, assume good intent. Disagreements are fine; rudeness isn't. Maintainers reserve the right to remove comments or close PRs that don't follow this.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers this project.

---

Thanks again — every contribution, no matter how small, helps make this tool better. 🙌
