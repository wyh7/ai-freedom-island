# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Season 1.x (current) | ✅ |

## Reporting a Vulnerability

This is a research project. We do not handle traditional software vulnerabilities.

However, if you find that:
1. An API key is accidentally exposed in the codebase
2. A tool implementation allows unintended side effects outside the simulation
3. The experiment results are being used in a way that violates the CC BY-NC 4.0 license

Please open a GitHub Issue or contact the maintainer directly.

## Important Notes on API Keys

**Never commit your `.env` file.** It is listed in `.gitignore` by default.

If you accidentally expose an API key:
1. Revoke it immediately from the provider's console
2. Generate a new key
3. Update your local `.env` file

The `.env.example` file contains only placeholder values — it is safe to commit.
