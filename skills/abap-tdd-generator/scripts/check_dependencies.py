#!/usr/bin/env python3
"""
Check (and try to auto-install) the dependencies this skill needs:
  - Python 3 itself (just reports the interpreter in use)
  - the `docx` (python-docx) module, used by insert_diagram.py to place
    the process-flow image into the .docx without touching raw OOXML
  - `matplotlib`, used by render_diagram_matplotlib.py to render the
    process-flow diagram (no Graphviz or other OS-level binary needed)

Run this BEFORE generating a .docx or a diagram. It never raises — it
always prints a JSON status block and exits 0, so the calling AI can
read the result and decide how to proceed (docx vs. markdown fallback,
diagram vs. text-only fallback) rather than the script crashing the
whole workflow.

Usage:
    python scripts/check_dependencies.py            # check + attempt installs
    python scripts/check_dependencies.py --no-install  # check only, no installs

Prints a single JSON object to stdout, e.g.:
    {
      "python_ok": true,
      "python_version": "3.12.3",
      "python_docx": {"available": true, "installed_now": false,
                       "error": null, "manual_instructions": null},
      "matplotlib": {"available": true, "installed_now": false,
                      "error": null, "manual_instructions": null}
    }

Both dependencies are plain pip packages — installing either never
needs admin rights or a system package manager, just
`pip install <package>` under whichever interpreter is resolved (see
SKILL.md's interpreter-resolution step). When an install genuinely
fails, the `manual_instructions` field carries the exact command to
retry — surface it to the user rather than only reporting "not
available".

Read `python_docx.available` before running insert_diagram.py or any
python-docx-based generation step. Read `matplotlib.available` before
attempting to render a diagram with render_diagram_matplotlib.py. If
either is false, follow the fallback instructions in SKILL.md — do not
retry silently and do not fabricate a diagram/document that skips the
missing piece without telling the user.
"""
import json
import subprocess
import sys


def _run(cmd, timeout=180):
    """Run a command, return (ok, stderr_tail). Never raises."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode == 0, proc.stderr.strip()[-500:]
    except FileNotFoundError:
        return False, f"'{cmd[0]}' not found"
    except Exception as e:  # noqa: BLE001
        return False, f"raised: {e}"


def _pip_install(package: str, timeout: int) -> dict:
    """Shared pip-install logic for any pure-Python dependency."""
    result = {"available": False, "installed_now": False, "error": None,
              "manual_instructions": None}

    ok, err = _run([sys.executable, "-m", "pip", "install", package,
                     "--break-system-packages", "--quiet"], timeout=timeout)
    if not ok:
        # --break-system-packages is a no-op flag pip rejects on some very
        # old pip versions — retry once without it before giving up.
        ok, err2 = _run([sys.executable, "-m", "pip", "install",
                          package, "--quiet"], timeout=timeout)
        if not ok:
            result["error"] = f"pip install failed: {err or err2}"
            result["manual_instructions"] = (
                f'Run this yourself, then retry: "{sys.executable} -m pip '
                f'install {package}"'
            )
            return result

    result["installed_now"] = True
    return result


def check_python_docx(try_install: bool) -> dict:
    result = {"available": False, "installed_now": False, "error": None,
              "manual_instructions": None}
    try:
        import docx  # noqa: F401
        result["available"] = True
        return result
    except ImportError:
        pass

    if not try_install:
        result["error"] = "python-docx not installed (install skipped: --no-install)"
        return result

    result = _pip_install("python-docx", timeout=120)
    if result["error"]:
        return result

    try:
        import docx  # noqa: F401
        result["available"] = True
    except ImportError as e:
        result["available"] = False
        result["error"] = f"still not importable after install: {e}"
        result["manual_instructions"] = (
            f'Run this yourself, then retry: "{sys.executable} -m pip '
            f'install python-docx"'
        )
    return result


def check_matplotlib(try_install: bool) -> dict:
    """matplotlib renders the process-flow diagram (see
    render_diagram_matplotlib.py) — a pure pip package with no separate
    OS-level binary to install, unlike Graphviz."""
    result = {"available": False, "installed_now": False, "error": None,
              "manual_instructions": None}
    try:
        import matplotlib  # noqa: F401
        result["available"] = True
        return result
    except ImportError:
        pass

    if not try_install:
        result["error"] = "matplotlib not installed (install skipped: --no-install)"
        return result

    result = _pip_install("matplotlib", timeout=180)
    if result["error"]:
        return result

    try:
        import matplotlib  # noqa: F401
        result["available"] = True
    except ImportError as e:
        result["available"] = False
        result["error"] = f"still not importable after install: {e}"
        result["manual_instructions"] = (
            f'Run this yourself, then retry: "{sys.executable} -m pip '
            f'install matplotlib"'
        )
    return result


def main():
    try_install = "--no-install" not in sys.argv

    status = {
        "python_ok": True,
        "python_version": sys.version.split()[0],
        "python_docx": check_python_docx(try_install),
        "matplotlib": check_matplotlib(try_install),
    }
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
