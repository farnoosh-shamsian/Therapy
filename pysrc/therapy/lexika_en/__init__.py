"""Lexika_en — die englischen Wortlisten, parallel zu :mod:`therapy.lexika`.

Eigenes Paket statt eines Unterordners in ``lexika/``: die deutschen Listen
bleiben damit an ihrem Platz und unverändert, und jeder Import sagt an der
Stelle, an der er steht, welche Sprache gemeint ist.

Die Gliederung ist absichtlich dieselbe wie im deutschen Paket — gleiche
Abschnitte, gleiche Reihenfolge, gleiche Schlüssel, wo die Sprachen dasselbe
messen. Wo sie es nicht tun, steht das im Quelltext und nicht in einer
Fussnote.
"""

from . import marker, emotion, funktion, dialogmuster  # noqa: F401
