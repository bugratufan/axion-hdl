import sys

_YELLOW = "\033[33m"
_RED    = "\033[31m"
_RESET  = "\033[0m"

def _supports_color():
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()

def warn(msg: str):
    if _supports_color():
        print(f"{_YELLOW}  Warning: {msg}{_RESET}", file=sys.stderr)
    else:
        print(f"  Warning: {msg}", file=sys.stderr)

def error(msg: str):
    if _supports_color():
        print(f"{_RED}  Error: {msg}{_RESET}", file=sys.stderr)
    else:
        print(f"  Error: {msg}", file=sys.stderr)
