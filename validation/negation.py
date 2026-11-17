
import re


def contains_explicit_negation(transcription):
    """
    Detect explicit negation of inspection commands.

    Used to reject negated commands before SLM processing.
    Does not authorize or dispatch missions.
    """

    if not isinstance(transcription, str):
        return False

    patterns = [
        r"\bDO\s+NOT\s+INSPECT\b",
        r"\bDON['’]?T\s+INSPECT\b",
    ]

    return any(
        re.search(pattern, transcription, flags=re.IGNORECASE)
        for pattern in patterns
    )
