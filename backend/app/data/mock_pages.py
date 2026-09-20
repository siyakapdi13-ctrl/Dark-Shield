"""
Synthetic e-commerce pages for demo mode.

`build_mock_page(url, rng)` returns deterministic HTML seeded from the URL so
the same URL always produces the same demo result. Pages mix clean and
manipulative components so Trust Scores span the full range.
"""
from __future__ import annotations

import random
from typing import List, Tuple
from urllib.parse import urlsplit

PRODUCTS = [
    ("Wireless Noise-Cancelling Headphones", 199, 349),
    ("Smart Fitness Watch Pro", 149, 299),
    ("Ergonomic Office Chair", 289, 599),
    ("4K Action Camera", 179, 429),
    ("Robot Vacuum Cleaner", 249, 699),
    ("Portable Espresso Maker", 89, 159),
    ("Mechanical Keyboard", 119, 189),
    ("Air Purifier HEPA", 159, 320),
]

SCARCITY = ['<span class="stock-alert">Only {n} left in stock!</span>', '<span class="badge">Limited stock — selling fast</span>', '<p class="alert">Almost gone! Last chance to order today.</p>']
URGENCY = ['<div class="countdown" id="deal-timer">Offer ends in 00:{m}:{s}</div>', '<p class="urgent">Hurry! Flash sale ends soon. Buy now!</p>', '<p>Limited time deal — today only.</p>']
SOCIAL = ["<p class=\"live\">{n} people are viewing this right now</p>", "<p class=\"live\">Someone in Mumbai just bought this</p>", "<p>{n} people have this in their cart</p>"]
CONFIRMSHAME = ['<div role="dialog" class="modal"><h3>Get 15% off your first order</h3><button>Yes, save me money</button><button class="link">No, I don\'t want to save money</button></div>',
                '<div role="dialog" class="modal"><h3>Protect your purchase</h3><button>Add protection</button><button class="link">No thanks, I\'d rather risk it</button></div>']
ADDONS = ['<label><input type="checkbox" name="protection" checked> Add 2-year Purchase Protection (+$24.99)</label>',
          '<label><input type="checkbox" name="priority" checked> Priority delivery (+$9.99)</label>',
          '<label><input type="checkbox" name="donation" checked> Round up and donate $1.00</label>',
          '<label><input type="checkbox" name="newsletter" checked> Subscribe to marketing emails</label>']
FEES = ['<tr><td>Service fee</td><td>$4.99</td></tr>', '<tr><td>Convenience fee</td><td>$2.49</td></tr>', '<tr><td>Handling fee</td><td>$3.95</td></tr>']
CONTINUITY = ['<p class="fine-print">Start your 7-day free trial. After trial, your subscription will automatically renew at $14.99/month unless cancelled.</p>',
              '<small>Cancel anytime by calling customer support during business hours.</small>']
CONSENT = ['<div class="cookie-banner"><p>We use cookies to personalise your experience.</p><button class="primary">Accept all</button><a class="tiny" style="opacity:0.4;font-size:9px">Manage preferences</a></div>']
DISCOUNT_TXT = ['<p class="deal"><s>Was ${orig}</s> <strong>${cur}</strong> <span>You save {pct}% off</span></p>', '<p>MRP <s>${orig}</s> Now ${cur} — {pct}% off list price</p>']
CLEAN = ['<p>Free returns within 30 days. No questions asked.</p>', '<p>All prices include taxes. Shipping calculated at checkout.</p>',
         '<p>Read our full refund policy. Contact support any time via chat or email.</p>', '<p>Secure payment. Your data is never shared with third parties.</p>',
         '<p>Cancel your subscription at any time from your account settings in one click.</p>']


def _site_profile(host: str, rng: random.Random) -> int:
    """0 = clean, 1 = moderate, 2 = aggressive. Certain keywords bias the profile."""
    h = host.lower()
    if any(w in h for w in ("deal", "flash", "cheap", "mega", "sale", "offer", "discount")):
        return 2
    if any(w in h for w in ("trust", "fair", "honest", "shop", "store", "official", "example")):
        return rng.choice([0, 1])
    return rng.choice([0, 1, 1, 2])


def build_mock_page(url: str, rng: random.Random) -> Tuple[str, str]:
    host = (urlsplit(url).hostname or "example.com").lower()
    brand = host.split(".")[-2].title() if "." in host else host.title()
    profile = _site_profile(host, rng)
    name, cur, orig = rng.choice(PRODUCTS)

    parts: List[str] = []
    parts.append(f"<header><nav><a href='/'>{brand}</a> <a href='/deals'>Deals</a> <a href='/help'>Help</a></nav></header>")
    parts.append(f"<main><h1>{name}</h1>")
    parts.append("<span class='sponsored'>Sponsored</span>" if profile == 2 and rng.random() < 0.5 else "")

    if profile == 0:
        parts.append(f"<p class='price'>${cur}</p>")
        parts.extend(rng.sample(CLEAN, 3))
        parts.append("<button>Add to cart</button><button>Buy</button>")
        if rng.random() < 0.4:
            parts.append(rng.choice(SOCIAL).format(n=rng.randint(2, 6)))
    else:
        pct = int(round((orig - cur) / orig * 100))
        if profile == 2:
            orig = int(cur * rng.uniform(2.6, 4.0))
            pct = int(round((orig - cur) / orig * 100))
        parts.append(rng.choice(DISCOUNT_TXT).format(orig=orig, cur=cur, pct=pct))
        parts.append(rng.choice(SCARCITY).format(n=rng.randint(1, 4 if profile == 2 else 9)))
        parts.append(rng.choice(URGENCY).format(m=rng.randint(5, 59), s=rng.randint(10, 59)))
        parts.append(rng.choice(SOCIAL).format(n=rng.randint(12, 87)))
        parts.append("<button class='cta'>Buy now</button><button class='cta'>Add to cart</button><button class='cta'>Get it today</button>")
        if profile == 2:
            parts.append("<button class='cta'>Claim deal</button><button class='cta'>Unlock offer</button><button class='cta'>Don't miss out</button>")
            parts.append(rng.choice(CONFIRMSHAME))
            parts.append(rng.choice(CONTINUITY))
            parts.append(rng.choice(CONSENT))
        elif rng.random() < 0.5:
            parts.append(rng.choice(CONFIRMSHAME))

        # checkout section
        parts.append("<section id='checkout'><h2>Order summary</h2><form>")
        for a in rng.sample(ADDONS, 2 if profile == 1 else 3):
            parts.append(a)
        parts.append("<table><tr><td>Item</td><td>$%d</td></tr>" % cur)
        for f in rng.sample(FEES, 1 if profile == 1 else 2):
            parts.append(f)
        parts.append("<tr><td>Shipping</td><td>+ shipping calculated later</td></tr></table>")
        parts.append("<small class='fine-print'>*Terms apply. Restrictions apply. See details.</small>")
        parts.append("<button type='submit'>Place order</button></form></section>")
        parts.extend(rng.sample(CLEAN, 1))

    parts.append("</main><footer><a href='/privacy'>Privacy</a> <a href='/terms'>Terms</a></footer>")
    title = f"{name} | {brand}"
    html = f"<!doctype html><html><head><title>{title}</title></head><body>{''.join(parts)}</body></html>"
    return html, title
