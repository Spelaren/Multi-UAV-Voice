
import re


def contains_explicit_cancellation(transcription):
    """
    Detect explicit cancellation phrases.

    Intended as a conservative pre-SLM rejection check.
    Does not authorize or dispatch missions.
    """

    if not isinstance(transcription, str):
        return False

    text = transcription.upper().strip()

    patterns = [
        r"\bCANCEL\s+(?:THAT|THE|THIS)\s+COMMAND\b",
        r"\bCANCEL\s+(?:THAT|THE|THIS)\s+MISSION\b",
        r"\bSTOP\s+(?:THAT|THE|THIS)\s+COMMAND\b",
        r"\bNEVER\s+MIND\b",
    ]

    return any(
        re.search(pattern, text)
        for pattern in patterns
    )
