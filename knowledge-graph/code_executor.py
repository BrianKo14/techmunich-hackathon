from typing import Any, Dict, Union

NumberOrString = Union[int, float, str]

def execute_snippet(code: str, /, **params: Any) -> NumberOrString:
    """
    Execute arbitrary Python `code` with keyword `params` injected into globals.
    Return the final value of the variable named `result` after execution.

    - If `result` is not defined by the code, raise ValueError.
    - If `result` is not an int/float/str, coerce to str and return that.

    SECURITY: Executes arbitrary code. Do NOT use with untrusted input.
    """
    env: Dict[str, Any] = {"__builtins__": __builtins__}
    env.update(params)

    exec(compile(code, "<user_code>", "exec"), env, None)  # intentional arbitrary exec

    if "result" not in env:
        raise ValueError("The snippet did not set a variable named 'result'.")

    out = env["result"]
    return out if isinstance(out, (int, float, str)) else str(out)
