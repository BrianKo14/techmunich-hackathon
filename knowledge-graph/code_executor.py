# WARNING: THIS PART OF THE CODE IS HIGHLY VULNERABLE TO CODE INJECTION ATTACKS. GIVE US THOSE MECHANICAL KEYBOARDS!

from typing import Any, Dict, Union
import inspect

NumberOrString = Union[int, float, str]

def execute_snippet(code: str, /, **params: Any) -> NumberOrString:
    """
    Execute arbitrary Python `code` with keyword `params` injected into globals.
    Return either:
      - the final value of a variable named `result` set by the code, OR
      - if `result` is not set, the return value of a function `answer(...)`
        defined by the code.

    Behavior:
    - If neither `result` nor a callable `answer` is present, raise ValueError.
    - If the final output is not int/float/str, coerce to str and return that.

    SECURITY: Executes arbitrary code. Do NOT use with untrusted input.
    """
    # Inject user params + ensure known_results exists for read-only use by code
    env: Dict[str, Any] = {"__builtins__": __builtins__}
    env.update(params)
    if "known_results" not in env:
        env["known_results"] = {}

    # Run the user module
    exec(compile(code, "<user_code>", "exec"), env, None)  # intentional arbitrary exec

    # 1) Preferred fast-path: explicit `result` set by the snippet
    if "result" in env:
        out = env["result"]
        return out if isinstance(out, (int, float, str)) else str(out)

    # 2) Fallback: call `answer(...)` if defined by the snippet
    fn = env.get("answer")
    if callable(fn):
        # Support either exact spec (answer(user_data)) or a permissive 2-arg form
        sig = inspect.signature(fn)
        params_len = len(sig.parameters)
        if params_len == 1:
            out = fn(env.get("user_data"))
        elif params_len == 2:
            # Graceful support if some code variants expect (user_data, known_results)
            out = fn(env.get("user_data"), env.get("known_results"))
        else:
            raise ValueError(
                "The function 'answer' must accept 1 or 2 parameters: "
                "(user_data) or (user_data, known_results)."
            )
        return out if isinstance(out, (int, float, str)) else str(out)

    # 3) Nothing to return
    raise ValueError(
        "The snippet must either set a variable named 'result' or define a callable 'answer'."
    )
