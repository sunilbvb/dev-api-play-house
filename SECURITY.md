# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| < 1.1   | :x:                |

## Zero Third-Party Dependency Security Guarantee

**Dev API Play House** relies 100% on the standard library of Python 3 (`http.server`, `urllib.request`, `sqlite3`, etc.) with zero third-party `pip` dependencies. This significantly eliminates supply-chain vulnerabilities, package poisoning attacks, and dependency audit rot.

## Reporting a Vulnerability

If you discover a security vulnerability or security bug, please responsibly disclose it by emailing the maintainer or opening a confidential security advisory on GitHub:

* **Repository**: [https://github.com/sunilbvb/dev-api-play-house/security/advisories](https://github.com/sunilbvb/dev-api-play-house/security/advisories)
* **Maintainer**: Sunil Bakale ([@sunilbvb](https://github.com/sunilbvb))

Please do **NOT** file public issues for critical security vulnerabilities until they have been patched and released.
