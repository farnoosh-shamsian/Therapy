"""Dialogmuster — Fragetypen und Rückkanal."""

from __future__ import annotations

MUSTER: dict[str, list[str]] = {
    # ---------------------------------------------------------------------------
    # Offene Fragen:
    # ---------------------------------------------------------------------------
    "frage_offen": [
        r"(^|[.?!]\s*)(wie|was|wann|wo|warum|wieso|weshalb|wer|wodurch|inwiefern|woran|wobei|wovon|womit)\b[^?]*\?",
        r"\berzählen sie\b", r"\bbeschreiben sie\b", r"\bmögen sie (mir )?erzählen\b",
        r"\bwas fällt ihnen\b", r"\bwas geht (ihnen )?(gerade )?(durch den kopf|vor)\b",
        r"\bwie ist das für sie\b", r"\bwas macht das mit ihnen\b",
        r"\bwo (spüren|merken) sie das\b", r"\bwie war das\b",
        r"\bmehr dazu\b\?", r"\bund dann\?",
    ],
    # ---------------------------------------------------------------------------
    # Geschlossene Fragen:
    # ---------------------------------------------------------------------------
    "frage_geschlossen": [
        r"(^|[.?!]\s*)(ist|sind|war|waren|haben|hat|hatten|können|könnten|wollen|wollten|würden|werden|dürfen|darf|soll|sollen|muss|müssen|gibt|geht|kommt|stimmt|finden|glauben|denken|meinen|kennen|fühlen)\s+(sie|es|das|der|die|ihr|ihnen|man)\b[^?]*\?",
        r"\b(oder)\?\s*$", r"\bnicht wahr\?", r"\brichtig\?\s*$", r"\bstimmt('s| das)?\?",
        r"\bja\?\s*$", r"\bja oder nein\b",
        r"\bhaben sie\b[^?]*\?", r"\bwaren sie\b[^?]*\?",
    ],
    # ------------------------------------------------------------------
    "rueckkanal": [
        r"^(mhm|hm+|aha|ach so|achso|ja|jaja|ja ja|genau|okay|ok|verstehe|klar|gut|richtig|stimmt)[.!,\s]*$",
        r"^(mhm[,.\s]*){1,3}$",
    ],
}
