import os
import re
from typing import Optional
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "o3") # We use a very capable model for code generation

_sys = (
    "You are a code generator. "
    "Return ONLY raw Python code. "
    "Do NOT use backticks, code fences, or language tags. "
    "Prefer concise, runnable examples."
    "Don't use classes."
    "IMPORTANT: The return value should be stored in a global variable named 'result'. (Global, i.e. no indentation)"
)

FENCE_BLOCK_RE = re.compile(r"^```[a-zA-Z0-9_+\-]*\n([\s\S]*?)\n```$", re.MULTILINE)
FENCE_INLINE_RE = re.compile(r"```([\s\S]*?)```", re.DOTALL)

def _strip_code_fences(text: str) -> str:
    # Prefer a full fenced block (with optional language tag)
    for m in FENCE_BLOCK_RE.finditer(text):
        inner = m.group(1).strip()
        if inner:
            return inner
    # Fallback: any inline fenced section
    inline = FENCE_INLINE_RE.findall(text)
    if inline:
        return inline[0].strip()
    # Nothing fenced—return as-is
    return text.strip()

client = OpenAI()  # reads OPENAI_API_KEY from env

def ask_for_code(prompt: str) -> str:
    """Send a natural-language request and get back raw code only (no ``` or language tag)."""

    resp = client.responses.create(
        model=MODEL,
        instructions=_sys,
        input=prompt,
    )
    return _strip_code_fences(resp.output_text)


def generate_node_summary(node_content: str) -> str:
    """Generate a short summary (variable name) for a node based on its content.
    Future code generation will use this summary to know when to reference this node buffer."""

    prompt = (
        "Generate a concise variable name (in snake_case) that summarizes the following content. "
        "The name should be descriptive yet brief."
        "Avoid generic names like 'data' or 'info'."
        "If the content is empty or meaningless, return 'untitled_node'.\n\n"
        f"Content:\n{node_content}\n\n"
        "Variable name:"
    )
    resp = client.responses.create(
        model=MODEL,
        instructions=_sys,
        input=prompt,
    )
    summary = resp.output_text.strip()
    if summary:
        # Sanitize to snake_case
        summary = re.sub(r"\W+", "_", summary).lower()
        return summary
    return None
