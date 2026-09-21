"""Dialogue patterns."""

from __future__ import annotations

MUSTER: dict[str, list[str]] = {
    # ---------------------------------------------------------------------------
    # Offene Fragen:
    # ---------------------------------------------------------------------------
    "frage_offen": [
        r"(^|[.?!]\s*)(what|how|when|where|why|who|which|in what way|to what extent)\b[^?]*\?",
        r"\btell me (about|more|what)\b", r"\bdescribe\b",
        r"\bwould you (tell|say) (me )?more\b", r"\bsay more\b",
        r"\bwhat comes (to mind|up)\b", r"\bwhat'?s going through your\b",
        r"\bwhat'?s that like (for you)?\b", r"\bhow is that for you\b",
        r"\bwhat does that do to you\b", r"\bwhere do you feel (that|it)\b",
        r"\bwhat was that like\b", r"\band then\?", r"\bgo on\b",
    ],
    # ---------------------------------------------------------------------------
    # Geschlossene Fragen:
    # ---------------------------------------------------------------------------
    "frage_geschlossen": [
        r"(^|[.?!]\s*)(is|are|was|were|do|does|did|have|has|had|can|could|will|would|shall|should|may|might|must)\s+(you|it|that|this|he|she|they|we|there)\b[^?]*\?",
        r"\b(or)\?\s*$", r"\bisn'?t it\?", r"\bdidn'?t (you|it|they)\?",
        r"\bright\?\s*$", r"\bdon'?t you\?", r"\bwasn'?t it\?",
        r"\byeah\?\s*$", r"\byes or no\b", r"\bcorrect\?\s*$",
        r"\bdo you\b[^?]*\?", r"\bwere you\b[^?]*\?", r"\bhave you\b[^?]*\?",
    ],
    # ------------------------------------------------------------------
    "rueckkanal": [
        r"^(mhm+|mm+|hm+|uh[- ]?huh|aha|ah|oh|yeah|yep|yup|yes|right|okay|ok|sure|i see|got it|exactly|indeed|true|quite)[.!,\s]*$",
        r"^(mhm[,.\s]*){1,3}$",
        r"^(right[,.\s]*){1,3}$",
    ],
}
