"""
Feature extraction – turns raw HTML (+ optional browser DOM data) into the
structured feature dictionary consumed by the detectors.

Uses BeautifulSoup for secondary parsing so it also works for the httpx and
mock scrapers (no browser).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from app.services.scraping_service import ScrapeResult

URGENCY_WORDS = ["now", "hurry", "soon", "today", "limited", "expires", "ends", "last chance", "don't miss", "flash", "quick"]
SCARCITY_WORDS = ["only", "left", "stock", "remaining", "almost gone", "selling fast", "few"]
GUILT_WORDS = ["don't want", "rather", "no thanks", "risk it", "hate", "prefer to pay", "miss out"]

_PRICE_RE = re.compile(r"([$€£₹])\s?(\d[\d,]*(?:\.\d{1,2})?)")
_TIMER_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
_CTA_WORDS = ("buy", "order", "get", "claim", "add to cart", "checkout", "subscribe", "unlock", "start", "join", "shop now")


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _to_num(s: str) -> Optional[float]:
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _guess_page_type(url: str, text_low: str) -> str:
    u = url.lower()
    if any(w in u for w in ("checkout", "cart", "basket", "payment")) or "order summary" in text_low:
        return "Checkout page"
    if any(w in u for w in ("pricing", "plans", "subscribe")):
        return "Pricing page"
    if any(w in u for w in ("product", "/p/", "/dp/", "item")):
        return "Product page"
    return "Product page" if "add to cart" in text_low else "Landing page"


def extract_features(scrape: ScrapeResult) -> Dict[str, Any]:
    soup = BeautifulSoup(scrape.html or "", "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    dom = scrape.dom_data or {}
    visible_text = _clean(dom.get("visibleText") or soup.get_text(" "))
    text_low = visible_text.lower()

    # Buttons / CTAs
    button_text: List[str] = dom.get("buttons") or [
        _clean(b.get_text() or b.get("value", "")) for b in soup.select("button, [role=button], input[type=submit], a.btn, a.cta, a.button")
    ]
    button_text = [b for b in button_text if b][:80]
    cta_count = sum(1 for b in button_text if any(w in b.lower() for w in _CTA_WORDS))

    # Links & labels
    link_text = [_clean(a.get_text()) for a in soup.find_all("a") if _clean(a.get_text())][:100]
    form_labels = [_clean(l.get_text()) for l in soup.find_all("label") if _clean(l.get_text())][:60]

    # Checkbox / radio state
    checkbox_state: List[Dict[str, Any]] = []
    radio_state: List[Dict[str, Any]] = []
    if dom.get("checkboxes"):
        for cb in dom["checkboxes"]:
            entry = {"label": _clean(cb.get("label", "")), "checked": bool(cb.get("checked")), "optional": not cb.get("required"), "selector": cb.get("selector")}
            (radio_state if cb.get("type") == "radio" else checkbox_state).append(entry)
    else:
        for inp in soup.select("input[type=checkbox], input[type=radio]"):
            label_el = inp.find_parent("label")
            label = _clean(label_el.get_text()) if label_el else _clean(inp.get("aria-label") or inp.get("name") or "")
            entry = {"label": label, "checked": inp.has_attr("checked"), "optional": not inp.has_attr("required"),
                     "selector": f"#{inp['id']}" if inp.get("id") else (f"[name=\"{inp['name']}\"]" if inp.get("name") else None)}
            (radio_state if inp.get("type") == "radio" else checkbox_state).append(entry)
    selected_addons = [c["label"] for c in checkbox_state if c["checked"] and c["optional"]]

    # Timers
    timer_elements: List[str] = dom.get("timers") or [
        _clean(el.get_text()) for el in soup.select("[class*=countdown], [class*=timer], [id*=countdown], [id*=timer]") if _clean(el.get_text())
    ]
    timer_elements = [t for t in timer_elements if _TIMER_RE.search(t) or "end" in t.lower() or "left" in t.lower()][:10]

    # Popups / modals
    popup_text: List[str] = dom.get("popups") or [
        _clean(el.get_text()) for el in soup.select("[role=dialog], .modal, [class*=popup], [class*=cookie]") if _clean(el.get_text())
    ]

    # Prices & discounts
    struck = dom.get("struck") or [_clean(s.get_text()) for s in soup.select("s, del, strike, [class*=strike], [class*=old-price], [class*=was-price]")]
    price_values: List[Dict[str, Any]] = []
    for row in soup.select("tr"):
        cells = [_clean(c.get_text()) for c in row.find_all(["td", "th"])]
        if len(cells) >= 2:
            m = _PRICE_RE.search(cells[-1])
            if m:
                price_values.append({"label": cells[0], "current": _to_num(m.group(2)), "currency": m.group(1)})
    for el in soup.select("[class*=price], [class*=deal], p"):
        txt = _clean(el.get_text())
        nums = [(_to_num(m.group(2)), m.group(1)) for m in _PRICE_RE.finditer(txt)]
        nums = [(n, c) for n, c in nums if n is not None]
        if len(nums) >= 2 and any(s and s in txt for s in struck):
            hi, lo = max(n for n, _ in nums), min(n for n, _ in nums)
            if hi > lo:
                price_values.append({"label": "Product price", "original": hi, "current": lo, "currency": nums[0][1]})
                break
    discount_values = [int(m.group(1)) for m in re.finditer(r"(\d{1,3})\s*%\s*off", text_low)]

    # Word signals
    urgency_words = [w for w in URGENCY_WORDS if w in text_low]
    scarcity_words = [w for w in SCARCITY_WORDS if w in text_low]
    guilt_words = [w for w in GUILT_WORDS if w in text_low]

    return {
        "url": scrape.final_url or scrape.url,
        "title": scrape.title or _clean(soup.title.get_text() if soup.title else ""),
        "page_type": _guess_page_type(scrape.url, text_low),
        "visible_text": visible_text[:60000],
        "button_text": button_text,
        "link_text": link_text,
        "form_labels": form_labels,
        "price_values": price_values[:30],
        "discount_values": discount_values[:20],
        "timer_elements": timer_elements,
        "popup_text": popup_text[:20],
        "checkbox_state": checkbox_state[:40],
        "radio_state": radio_state[:40],
        "selected_addons": selected_addons,
        "cta_count": cta_count,
        "urgency_words": urgency_words,
        "scarcity_words": scarcity_words,
        "guilt_words": guilt_words,
        "small_text": (dom.get("smallText") or [_clean(s.get_text()) for s in soup.select("small, .fine-print, sup")])[:20],
        "low_contrast_controls": (dom.get("lowContrast") or [])[:20],
        "stats": {
            "text_length": len(visible_text),
            "buttons": len(button_text),
            "links": len(link_text),
            "forms": len(soup.find_all("form")),
            "checkboxes": len(checkbox_state),
            "prechecked": len(selected_addons),
            "timers": len(timer_elements),
            "popups": len(popup_text),
        },
    }


def feature_summary(features: Dict[str, Any]) -> Dict[str, Any]:
    """Compact, JSON-safe subset stored with the analysis."""
    return {
        "pageType": features["page_type"],
        "title": features["title"],
        "ctaCount": features["cta_count"],
        "prices": features["price_values"][:10],
        "discounts": features["discount_values"][:10],
        "timers": features["timer_elements"][:5],
        "selectedAddons": features["selected_addons"][:10],
        "urgencyWords": features["urgency_words"],
        "scarcityWords": features["scarcity_words"],
        "guiltWords": features["guilt_words"],
        "buttons": features["button_text"][:20],
        "stats": features["stats"],
    }
