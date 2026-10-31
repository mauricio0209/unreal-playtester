"""Deterministic interpreter for model-written checks.

Model output is untrusted: this module never uses ``eval``, ``exec`` or
anything that runs code. See ``agent/checks_reference.md`` for the language.
"""

import math
import re

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_PATH_RE = re.compile(r"^[A-Za-z0-9_]+(\.[A-Za-z0-9_]+)*$")

_DID_ACTIONS = ("move_to", "look_at", "jump", "interact", "step")

_COMPARISONS = ("==", "!=", "<", "<=", ">", ">=")
_ARITHMETIC = ("+", "-")
_LOGIC_LIST = ("and", "or")
_TEMPORAL_SINGLE = ("not", "ever", "always", "final")

KNOWN_OPERATORS = frozenset(
    ["var", "prev", "first", "did", "dist"]
    + list(_COMPARISONS)
    + list(_ARITHMETIC)
    + list(_LOGIC_LIST)
    + list(_TEMPORAL_SINGLE)
    + ["after"]
)

MAX_DEPTH = 12
MAX_NODES = 200
MAX_DESCRIPTION_LEN = 500
MAX_STRING_LITERAL_LEN = 200


def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_expr(expr, _depth_guard=0):
    """Validate one expression; return (depth, nodes). Raise ValueError."""
    if _depth_guard > 1000:
        raise ValueError("expression too deep")
    if expr is None or isinstance(expr, bool):
        return (1, 1)
    if isinstance(expr, (int, float)):
        return (1, 1)
    if isinstance(expr, str):
        if len(expr) > MAX_STRING_LITERAL_LEN:
            raise ValueError("string literal too long")
        return (1, 1)
    if not isinstance(expr, dict):
        raise ValueError("invalid expression")
    if len(expr) != 1:
        raise ValueError("expression must have exactly one key")
    op = next(iter(expr))
    if op not in KNOWN_OPERATORS:
        raise ValueError(f"unknown operator: {op!r}")
    arg = expr[op]
    if op in ("var", "prev", "first"):
        if not isinstance(arg, str) or not _PATH_RE.match(arg):
            raise ValueError(f"invalid path for {op!r}")
        return (1, 1)
    if op == "did":
        if arg not in _DID_ACTIONS:
            raise ValueError(f"invalid action for 'did': {arg!r}")
        return (1, 1)
    if op == "dist":
        if (
            not isinstance(arg, list)
            or len(arg) != 2
            or any(not isinstance(p, str) or not _PATH_RE.match(p) for p in arg)
        ):
            raise ValueError("invalid paths for 'dist'")
        return (1, 1)
    if op in _COMPARISONS or op in _ARITHMETIC:
        if not isinstance(arg, list) or len(arg) != 2:
            raise ValueError(f"operator {op!r} needs a list of two expressions")
        depths_nodes = [_validate_expr(e, _depth_guard + 1) for e in arg]
        depth = 1 + max(d[0] for d in depths_nodes)
        nodes = 1 + sum(d[1] for d in depths_nodes)
        return (depth, nodes)
    if op in _LOGIC_LIST:
        if not isinstance(arg, list) or len(arg) == 0:
            raise ValueError(f"operator {op!r} needs a non-empty list")
        depths_nodes = [_validate_expr(e, _depth_guard + 1) for e in arg]
        depth = 1 + max(d[0] for d in depths_nodes)
        nodes = 1 + sum(d[1] for d in depths_nodes)
        return (depth, nodes)
    if op in _TEMPORAL_SINGLE:
        depth_c, nodes_c = _validate_expr(arg, _depth_guard + 1)
        return (depth_c + 1, nodes_c + 1)
    if op == "after":
        if not isinstance(arg, list) or len(arg) != 2:
            raise ValueError("operator 'after' needs a list of two expressions")
        depths_nodes = [_validate_expr(e, _depth_guard + 1) for e in arg]
        depth = 1 + max(d[0] for d in depths_nodes)
        nodes = 1 + sum(d[1] for d in depths_nodes)
        return (depth, nodes)
    raise ValueError(f"unknown operator: {op!r}")


def validate(check) -> None:
    """Validate a check dict; raise ValueError on any problem."""
    if not isinstance(check, dict):
        raise ValueError("check must be a dict")
    if set(check.keys()) != {"id", "description", "violation"}:
        raise ValueError("check must have exactly keys 'id', 'description', 'violation'")
    check_id = check["id"]
    if not isinstance(check_id, str) or not _ID_RE.match(check_id):
        raise ValueError(f"invalid id: {check_id!r}")
    description = check["description"]
    if (
        not isinstance(description, str)
        or len(description) == 0
        or len(description) > MAX_DESCRIPTION_LEN
    ):
        raise ValueError("invalid description")
    try:
        depth, nodes = _validate_expr(check["violation"])
    except RecursionError:
        raise ValueError("expression too deep")
    if depth > MAX_DEPTH:
        raise ValueError("expression too deep")
    if nodes > MAX_NODES:
        raise ValueError("expression too large")


def _lookup_path(state, path: str):
    if not isinstance(state, dict):
        return None
    current = state
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _state_at(trace, index):
    if not isinstance(trace, list) or not 0 <= index < len(trace):
        return None
    entry = trace[index]
    if not isinstance(entry, dict):
        return None
    return entry.get("state")


def _lookup_at(trace, index, path: str):
    return _lookup_path(_state_at(trace, index), path)


def _kind(value: str) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "other"


def _equals(a, b) -> bool:
    kind_a, kind_b = _kind(a), _kind(b)
    if kind_a != kind_b:
        return False
    if kind_a == "null":
        return True
    if kind_a == "number":
        try:
            return bool(a == b)
        except Exception:
            return False
    try:
        return bool(a == b)
    except Exception:
        return False


def _location_xyz(value):
    if not isinstance(value, dict):
        return None
    try:
        x, y, z = value["X"], value["Y"], value["Z"]
    except (KeyError, TypeError):
        return None
    if not (_is_num(x) and _is_num(y) and _is_num(z)):
        return None
    return (x, y, z)


def _eval(expr, trace, index):
    n = len(trace)
    if isinstance(expr, dict):
        if len(expr) != 1:
            raise ValueError("expression must have exactly one key")
        op = next(iter(expr))
        arg = expr[op]
        if op == "var":
            return _lookup_at(trace, index, arg)
        if op == "prev":
            if index <= 0:
                return None
            return _lookup_at(trace, index - 1, arg)
        if op == "first":
            return _lookup_at(trace, 0, arg)
        if op == "did":
            if not 0 <= index < n:
                return False
            entry = trace[index]
            if not isinstance(entry, dict):
                return False
            action = entry.get("action")
            return isinstance(action, dict) and action.get("action") == arg
        if op == "dist":
            first_loc = _lookup_at(trace, index, arg[0])
            second_loc = _lookup_at(trace, index, arg[1])
            a = _location_xyz(first_loc)
            b = _location_xyz(second_loc)
            if a is None or b is None:
                return None
            try:
                return float(math.dist(a, b))
            except Exception:
                return None
        if op == "==":
            return bool(_equals(_eval(arg[0], trace, index), _eval(arg[1], trace, index)))
        if op == "!=":
            return bool(not _equals(_eval(arg[0], trace, index), _eval(arg[1], trace, index)))
        if op in ("<", "<=", ">", ">="):
            left = _eval(arg[0], trace, index)
            right = _eval(arg[1], trace, index)
            if not (_is_num(left) and _is_num(right)):
                return False
            try:
                if op == "<":
                    return bool(left < right)
                if op == "<=":
                    return bool(left <= right)
                if op == ">":
                    return bool(left > right)
                return bool(left >= right)
            except Exception:
                return False
        if op in ("+", "-"):
            left = _eval(arg[0], trace, index)
            right = _eval(arg[1], trace, index)
            if not (_is_num(left) and _is_num(right)):
                return None
            try:
                return left + right if op == "+" else left - right
            except Exception:
                return None
        if op == "and":
            return bool(all(bool(_eval(e, trace, index)) for e in arg))
        if op == "or":
            return bool(any(bool(_eval(e, trace, index)) for e in arg))
        if op == "not":
            return bool(not bool(_eval(arg, trace, index)))
        if op == "ever":
            return bool(any(bool(_eval(arg, trace, i)) for i in range(n)))
        if op == "always":
            return bool(all(bool(_eval(arg, trace, i)) for i in range(n)))
        if op == "final":
            if n == 0:
                return False
            return bool(bool(_eval(arg, trace, n - 1)))
        if op == "after":
            if n < 2:
                return False
            if not bool(_eval(arg[1], trace, n - 1)):
                return False
            return bool(any(bool(_eval(arg[0], trace, i)) for i in range(n - 1)))
        raise ValueError(f"unknown operator: {op!r}")
    return expr


def evaluate(trace, expr) -> bool:
    """Evaluate a validated expression at the last trace index."""
    try:
        n = len(trace)
    except TypeError:
        return False
    if n == 0:
        return False
    try:
        value = _eval(expr, trace, n - 1)
    except ValueError:
        raise
    except Exception:
        return False
    return bool(value) if value is not None else False


def dsl_violation(trace, params, spec) -> bool:
    """Verifier predicate: evaluate ``params["expr"]`` over the trace."""
    return evaluate(trace, params["expr"])
