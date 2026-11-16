import re


def normalize_pallet_identifiers(transcription):
    """
    Normalize simple formatting variations in pallet IDs.

    Examples:
        P-05 -> P05
        P 05 -> P05

    Does not validate pallet existence or authorize missions.
    """

    if not isinstance(transcription, str):
        return transcription

    return re.sub(
        r"\bP[\s-]+(\d{2})\b",
        r"P\1",
        transcription,
        flags=re.IGNORECASE
    )
