# SPDX-License-Identifier: AGPL-3.0-only
"""The launcher's language (Spanish or English), applied where texts are SHOWN.

The code of the launcher is written with Spanish texts. Instead of changing every place that makes one, the widgets and dialogs ask
`t(text)` for what to show: Spanish returns it unchanged; English looks it up in `i18n_en` (exact text, then texts with a value inside,
then known phrases inside a longer text). What the logic reads back from a widget is the original text, so nothing that compares texts
changes. A text that has no English yet is shown in Spanish (and `missing()` lists them, for the tests).
"""

import re

_lang = "es"
_cache = {}
_missing = set()
_tables = None
_SPLIT = re.compile(r"^(\s*)(.*?)(\s*)$", re.S)
_ICON = re.compile(r"^[^\w¿¡]+\s*")  # the emoji or symbol a text starts with
_BULB = "💡"
_SPANISH_HINT = re.compile(r"[áéíóúñ¿¡]|\b(el|la|los|las|de|que|para|con|una|tu|su|se|no|pulsa|juego)\b", re.I)


def set_language(lang):
    global _lang
    _lang = "en" if lang == "en" else "es"
    _cache.clear()


def language():
    return _lang


def missing():
    """Spanish-looking texts asked for in English that have no translation (what the tests look at)."""
    return sorted(_missing)


def _load():
    global _tables
    if _tables is not None:
        return _tables
    import i18n_en

    exact = dict(i18n_en.EXACT)
    templates = []
    for es, en in i18n_en.TEMPLATES:
        parts = es.split("{}")
        literal = sum(len(p) for p in parts)
        if literal < 3:
            continue
        rx = re.compile("(.*?)".join(re.escape(p) for p in parts), re.S)
        templates.append((literal, rx, en.split("{}")))
    templates.sort(key=lambda x: -x[0])
    # the same texts without the icon they start with (a tooltip puts a bulb where a label had another icon)
    bare = {}
    for es, en in exact.items():
        a, b = _ICON.sub("", es), _ICON.sub("", en)
        if a and a != es:
            bare.setdefault(a, b)
    phrases = sorted((k for k in exact if len(k) >= 14), key=len, reverse=True)
    _tables = (exact, templates, bare, phrases)
    return _tables


def _fill(pieces, values):
    out = [pieces[0]]
    for v, p in zip(values, pieces[1:]):
        out.append(v)
        out.append(p)
    return "".join(out)


def _line(core):
    exact, templates, bare, phrases = _load()
    hit = exact.get(core)
    if hit is not None:
        return hit
    lit = exact.get(f"{_BULB} {core}")  # a tooltip is the text of a "💡 ..." hint without its bulb
    if lit is not None:
        return lit[len(_BULB):].strip()
    if core.startswith(_BULB):
        rest = core[len(_BULB):].strip()
        hit = exact.get(rest) or bare.get(rest)
        if hit is None:
            hit = _line(rest) if rest != core else None
        if hit is not None and hit != rest:
            return f"{_BULB} {hit}"
    for _, rx, pieces in templates:
        m = rx.fullmatch(core)
        if m:
            return _fill(pieces, [_core(g) for g in m.groups()])
    # known phrases inside a longer text
    out = core
    for k in phrases:
        if k in out:
            out = out.replace(k, exact[k])
    return out


def _core(core):
    if not core:
        return core
    if "\n" in core:
        whole = _load()[0].get(core)
        if whole is not None:
            return whole
        for _, rx, pieces in _load()[1]:
            m = rx.fullmatch(core)
            if m:
                return _fill(pieces, [_core(g) for g in m.groups()])
        return "\n".join(_core(part) for part in core.split("\n"))
    return _line(core)


def t(text):
    """What to show for `text` in the chosen language."""
    if _lang != "en" or not text or not isinstance(text, str):
        return text
    hit = _cache.get(text)
    if hit is not None:
        return hit
    lead, core, trail = _SPLIT.match(text).groups()
    out = lead + _core(core) + trail if core else text
    if out == text and _SPANISH_HINT.search(core) and core not in _load()[0]:
        _missing.add(core)
    if len(_cache) > 8192:
        _cache.clear()
    _cache[text] = out
    return out
