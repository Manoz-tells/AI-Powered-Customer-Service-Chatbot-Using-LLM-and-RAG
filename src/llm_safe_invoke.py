from typing import Callable, Any


def safe_llm_invoke(
    invoke_function: Callable[[], Any],
    fallback_response: str
) -> tuple[str, bool]:

    try:
        result = invoke_function()

        if hasattr(result, "content"):
            content = result.content

            if isinstance(content, list):
                content = "".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                )

            return str(content).strip(), False

        return str(result).strip(), False

    except Exception as e:

        error_text = str(e).lower()

        quota_error = (
            "429" in error_text
            or "resource_exhausted" in error_text
            or "quota" in error_text
            or "rate limit" in error_text
        )

        temporary_error = (
            "503" in error_text
            or "unavailable" in error_text
            or "service unavailable" in error_text
        )

        if quota_error or temporary_error:
            print(
                "\n[LLM FALLBACK]"
                "\nGemini service temporarily unavailable."
            )

            return fallback_response, True

        raise