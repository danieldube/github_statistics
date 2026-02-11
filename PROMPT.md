You are an implementation agent working on the `github_statistics` project.

Context:
- The project specification, architecture, roles, and constraints are described in `AGENTS.md`.
- The step-by-step implementation plan is described in `TASKS.md`.
- The project is to be developed test-driven (tests first, then implementation).
- The project must support Python 3.8+.

Your goal in this run:
1. Open and read `TASKS.md`.
2. Identify the **next open step** that has not yet been fully implemented and integrated. Treat tasks strictly in order; do not redo completed steps unless they must be adjusted as a direct consequence of your current step.
3. Open and read `AGENTS.md` and use it to:
    - Understand the architecture, roles, and module responsibilities.
    - Ensure your implementation fits into the specified design and responsibilities (e.g., which module/file should contain which logic).
    - Respect all global constraints and non-functional requirements.

For the selected next step from `TASKS.md`:

A. Analyze and clarify
- Restate the step in your own words.
- Derive concrete acceptance criteria for this step (what must be true for it to be considered “done” and commit-ready).
- Identify which modules/files need to be created or modified.
- Identify which tests are required to validate this step fully.

B. Test-driven implementation
1. **Design and write tests first**:
    - Add or extend tests under `tests/` to fully cover the behavior required by this step, based on `AGENTS.md` and `TASKS.md`.
    - Tests must be deterministic, fast, and independent of real network or external systems where applicable.
    - Explicitly show all test file changes as complete file contents (not just snippets).
2. **Then implement functionality**:
    - Modify or create production code files (e.g., in `github_statistics/`) to make these new/updated tests pass.
    - Keep responsibilities aligned with `AGENTS.md` (e.g., config handling in `config.py`, CLI in `cli.py`, stats in `stats.py`, etc.).
    - Ensure compatibility with Python 3.8+ (no features newer than 3.8).
3. If needed for this step, update or create documentation within the repo (e.g., docstrings, inline comments, or README sections) so that usage and behavior are clear.

C. Commit-ready state
- Ensure your changes, considered as a whole, would be suitable for a single atomic git commit implementing this step.
- Make sure:
    - All tests related to this step are expected to pass.
    - Style is consistent with standard Python practices (PEP 8) and with any existing project style.
    - There are no “TODO”/“FIXME” placeholders directly related to this step.
- If you introduce new dependencies, note them clearly (e.g., as comments indicating they must be added to `pyproject.toml` / `setup.cfg`).

D. Output format
- First, briefly summarize:
    - Which step from `TASKS.md` you implemented.
    - The acceptance criteria you used.
- Then provide a **patch-style description of changes**, grouped by file:
    - For each affected file, output the **full final content** of the file (not a diff), inside a fenced code block labeled with the path, for example:
        - `# File: github_statistics/config.py`
        - ```python
         <full file content>
         ```
    - Include all new/modified test files under `tests/`.
    - Include any new/modified project files under `github_statistics/` and any relevant top-level files (e.g., `pyproject.toml`, `README.md`) if they are part of this step.

Constraints and reminders:
- Follow the test-first approach rigorously: tests must conceptually precede implementation, even though you will present everything at once.
- Do not skip steps in `TASKS.md`; always work on the next open one.
- Do not invoke or rely on real network access; all HTTP calls must remain mockable and not be exercised against live GitHub in tests.
- Always keep Python 3.8+ compatibility in mind.

Now, perform this process and present your complete, commit-ready changes for the next open step from `TASKS.md`.

Don't start with the another step automatically; wait for the next instruction after this output.
