# Contributing to Attendance Reminder

Thank you for your interest in this project.

Whether you are submitting a bug report, suggesting a feature, improving documentation, or writing code — every contribution is appreciated.

This repository is maintained by a solo developer who built this tool to solve a real problem. If you found it useful enough to want to improve it, that means something.

---

## Project Philosophy

This project exists to solve real-world problems for people who work overnight shifts.

Every feature should improve everyday productivity. If a feature does not make someone's shift easier, it does not belong here.

Avoid unnecessary complexity. The best code is the code you do not have to debug at 3 AM.

Stability always comes before new features. A working application that does one thing well is more valuable than a broken application that does ten things.

Commander Ralph — the long-term vision for this project — should evolve gradually through meaningful, reliable improvements. Not through rewrites.

---

## Before You Start

Read these documents first:

- **README.md** — understand what this project is and why it exists.
- **CHANGELOG.md** — see what has already changed.
- **DEVLOG.md** — understand the journey and the thinking behind decisions.

If you understand the long-term vision, your contributions will naturally fit into the project's direction.

---

## Branch Strategy

Never work directly on `main`. That branch contains stable releases only.

Use descriptive branch names with prefixes:

| Prefix | Purpose |
|--------|---------|
| `feature/` | New functionality |
| `bugfix/` | Bug fixes |
| `hotfix/` | Urgent production fixes |
| `docs/` | Documentation changes |

Examples:

```
feature/voice-pack
feature/calendar-sync
bugfix/logout-reminder-loop
docs/update-readme
```

Branch off `develop` for features and bug fixes. Branch off `main` only for hotfixes.

---

## Commit Messages

Write meaningful commit messages that explain what changed and why.

```
feat: add reminder history view

fix: resolve work preparation reminder loop

docs: update installation guide

refactor: simplify scheduler logic
```

If a commit needs more explanation, add a body. But keep the subject line clear and descriptive.

---

## Pull Requests

Pull requests should:

- Solve one problem. Do not combine unrelated changes.
- Remain focused on the issue they address.
- Include testing notes — what you verified and how.
- Update documentation when necessary.
- Avoid formatting changes or refactoring that is not related to the fix.

If a pull request touches multiple concerns, split it into separate PRs.

---

## Code Style

- Follow PEP8.
- Use type hints for all function signatures.
- Write docstrings for public methods and complex logic.
- Use meaningful variable and function names.
- Keep functions small and focused.
- Avoid duplicated code. If you are copying logic, extract it.
- Use logging instead of print statements.
- Comment why, not what. The code should communicate what it does.

---

## Testing

Before submitting any code, verify that:

- Reminders fire at the correct times.
- The scheduler respects DST settings.
- State persistence survives restarts.
- Settings save, load, import, and export correctly.
- The tray icon shows the correct status.
- Logs contain useful debugging information.

Never submit untested code. If you cannot test a change, explain why in the pull request description.

---

## Documentation

Whenever you add a feature:

- Update README.md if the feature affects how someone uses the application.
- Update CHANGELOG.md with a clear entry under the appropriate version.
- Consider whether DEVLOG.md should include the milestone.

Documentation is not optional. If a feature is not documented, it does not exist for most users.

---

## Feature Requests

Before suggesting a feature, ask yourself:

- Does this feature solve a real problem?
- Would Future Ralph actually use this?
- Does it move the project closer to Commander Ralph?

If the answer to any of these is no, reconsider whether the feature belongs here.

Feature requests are welcome. Open an issue and explain the problem you are trying to solve, not just the solution you have in mind.

---

## Bug Reports

When reporting a bug, include:

- Windows version
- Python version (if running from source)
- Relevant log entries from `attendance_reminder.log`
- Steps to reproduce the issue
- What you expected to happen
- What actually happened
- Screenshots if the bug is visual

Good bug reports save hours of back-and-forth. Thank you for writing them well.

---

## Security

Do not commit:

- API keys
- Passwords
- Personal credentials
- Configuration files containing sensitive information

If you accidentally commit sensitive data, notify the maintainer immediately.

---

## Vision

Commander Ralph is intended to become a personal desktop operations assistant — a tool that quietly manages reminders, schedules, tasks, and eventually more.

Every contribution should move the project one step closer to that vision without sacrificing the reliability that makes this application useful today.

---

## Engineering Principle

When in doubt, choose the simpler solution.

Reliable software that quietly works every day is more valuable than complicated software that impresses once.

Every feature should earn its place.

---

Thank you for helping build something that makes the overnight shift a little less stressful.

This project started because one person needed a tool that did not exist. Every contribution — whether code, documentation, a bug report, or even just a thoughtful suggestion — helps ensure that the next person who needs it does not have to build it from scratch.
