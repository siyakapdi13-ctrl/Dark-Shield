"""
Dark pattern catalog.

Single source of truth for pattern names, categories, severity defaults,
consumer-friendly explanations and recommendations. Used by the rule engine,
explanation service, trust-score service and AI assistant.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PatternDefinition:
    key: str
    name: str
    category: str                 # trust score category impacted most
    default_severity: str         # "High" | "Medium" | "Low"
    penalty: float                # base trust penalty (0-100 scale) at confidence 1.0
    reason: str
    explanation: str
    recommendation: str
    keywords: List[str]


PATTERNS: Dict[str, PatternDefinition] = {
    "fake_scarcity": PatternDefinition(
        key="fake_scarcity", name="Fake Scarcity", category="marketing_pressure", default_severity="High", penalty=12,
        reason="Scarcity wording creates urgency by suggesting the product may run out.",
        explanation="Messages like 'Only 2 left!' may pressure you into making a faster purchasing decision. Stock counters are sometimes generated rather than reflecting real inventory.",
        recommendation="Verify availability independently (e.g. revisit later or check other sellers) before purchasing.",
        keywords=["only {n} left", "limited stock", "selling fast", "almost gone", "low stock", "last chance", "few remaining", "hurry, only"],
    ),
    "urgency": PatternDefinition(
        key="urgency", name="Urgency Language", category="marketing_pressure", default_severity="Medium", penalty=8,
        reason="Time-pressure language and countdowns discourage careful comparison.",
        explanation="Phrases such as 'Offer ends soon' or countdown timers can trigger a fear of missing out. Many timers reset on refresh and are not tied to a real deadline.",
        recommendation="Refresh the page or return later to see whether the timer or offer is genuine. Take time to compare prices.",
        keywords=["buy now", "act now", "offer ends", "ends soon", "hurry", "limited time", "today only", "don't miss out", "expires in", "flash sale", "deal ends"],
    ),
    "countdown_timer": PatternDefinition(
        key="countdown_timer", name="Fake Countdown Timer", category="marketing_pressure", default_severity="High", penalty=10,
        reason="A countdown element was detected next to pricing or checkout actions.",
        explanation="Countdown timers create artificial urgency. If a timer restarts when you reload the page, it is not a real deadline.",
        recommendation="Reload the page to check whether the timer resets. Do not let a timer rush your decision.",
        keywords=["countdown", "timer", "time left", "remaining"],
    ),
    "confirmshaming": PatternDefinition(
        key="confirmshaming", name="Confirmshaming", category="ui_fairness", default_severity="Medium", penalty=8,
        reason="The decline option uses guilt- or shame-oriented wording.",
        explanation="Confirmshaming makes the option to opt out sound foolish or irresponsible (e.g. 'No, I don't want to save money'). It nudges you emotionally rather than informing you.",
        recommendation="Ignore the tone of the wording and decide based on what you actually need.",
        keywords=["no, i don't want", "no thanks, i", "i don't want to save", "i'd rather pay", "i don't like", "no, i prefer", "i hate", "i don't care about"],
    ),
    "hidden_charges": PatternDefinition(
        key="hidden_charges", name="Hidden Charges", category="checkout_transparency", default_severity="High", penalty=14,
        reason="Additional fees or charges appear that were not part of the advertised price.",
        explanation="Service fees, handling fees or 'convenience' charges added late in checkout make the real price hard to compare in advance.",
        recommendation="Review the full order summary before paying and compare the total, not the headline price.",
        keywords=["service fee", "convenience fee", "handling fee", "processing fee", "additional charges", "extra charges", "fees may apply", "surcharge", "platform fee", "booking fee"],
    ),
    "preselected_addons": PatternDefinition(
        key="preselected_addons", name="Pre-selected Add-on", category="checkout_transparency", default_severity="High", penalty=12,
        reason="An optional paid product or service is selected by default.",
        explanation="Pre-checked add-ons (insurance, warranties, donations, subscriptions) rely on you not noticing them. This is sometimes called 'sneak into basket'.",
        recommendation="Inspect every checkbox and line item in your cart before checkout and untick what you did not choose.",
        keywords=["add protection", "protect your purchase", "extended warranty", "insurance", "add to order", "yes, add", "premium support", "priority delivery"],
    ),
    "misleading_discount": PatternDefinition(
        key="misleading_discount", name="Misleading Discount", category="pricing_clarity", default_severity="Medium", penalty=10,
        reason="The discount presentation appears inflated or the reference price looks artificial.",
        explanation="A very large crossed-out 'original' price may never have been charged. Inflated reference prices make an ordinary price look like a bargain.",
        recommendation="Check the product's price history or other retailers before trusting a discount percentage.",
        keywords=["was $", "was ₹", "mrp", "you save", "% off", "list price", "regular price", "compare at"],
    ),
    "misleading_pricing": PatternDefinition(
        key="misleading_pricing", name="Misleading Pricing", category="pricing_clarity", default_severity="Medium", penalty=8,
        reason="Prices are shown in a way that obscures the actual total (drip pricing, per-month framing, excluded taxes).",
        explanation="Showing '$9/mo' without the annual commitment, or prices excluding tax and shipping, understates what you will actually pay.",
        recommendation="Look for the total price including taxes, fees and any minimum commitment.",
        keywords=["excl. tax", "plus taxes", "starting at", "from $", "per month*", "billed annually", "shipping not included", "+ shipping"],
    ),
    "forced_continuity": PatternDefinition(
        key="forced_continuity", name="Forced Continuity", category="transparency", default_severity="High", penalty=12,
        reason="A free trial or offer silently converts into a paid subscription.",
        explanation="Forced continuity charges you after a trial unless you actively cancel, and cancellation details are often hard to find.",
        recommendation="Note the trial end date, check how to cancel before signing up, and consider a virtual card.",
        keywords=["free trial", "auto-renew", "automatically renew", "cancel anytime", "after trial", "will be charged", "recurring", "subscription will continue"],
    ),
    "obstruction": PatternDefinition(
        key="obstruction", name="Obstruction / Difficult Cancellation", category="transparency", default_severity="Medium", penalty=8,
        reason="Cancelling or opting out appears to require significantly more effort than signing up.",
        explanation="'Roach motel' designs make it easy to get in and hard to get out — e.g. cancel only by phone, or through many confirmation screens.",
        recommendation="Before subscribing, locate the cancellation process. If it is unclear, treat that as a warning sign.",
        keywords=["call to cancel", "contact support to cancel", "cancellation request", "retention offer", "are you sure you want to leave", "before you go"],
    ),
    "disguised_ad": PatternDefinition(
        key="disguised_ad", name="Disguised Advertisement", category="transparency", default_severity="Low", penalty=5,
        reason="Promotional content is styled to look like organic content or navigation.",
        explanation="Ads dressed as regular results or 'recommended' items blur the line between advice and advertising.",
        recommendation="Look for small 'Sponsored' or 'Ad' labels and treat those items as advertising.",
        keywords=["sponsored", "promoted", "recommended for you", "partner offer", "advertisement"],
    ),
    "bait_and_switch": PatternDefinition(
        key="bait_and_switch", name="Bait-and-Switch Indicator", category="pricing_clarity", default_severity="Medium", penalty=8,
        reason="The advertised offer differs from what is actually available at checkout.",
        explanation="A headline offer attracts you, but the product is unavailable or the terms change once you are committed.",
        recommendation="Confirm the exact item, variant and price at the final checkout step match what was advertised.",
        keywords=["out of stock", "similar item", "alternative", "no longer available", "price has changed", "upgrade to"],
    ),
    "social_pressure": PatternDefinition(
        key="social_pressure", name="Social-Pressure Messaging", category="marketing_pressure", default_severity="Low", penalty=6,
        reason="Activity messages (\"12 people are viewing this\") are used to pressure the decision.",
        explanation="Live viewer counts and 'someone just bought' notifications may be fabricated or randomly generated to create a sense of competition.",
        recommendation="Treat activity notifications as marketing, not as information about real demand.",
        keywords=["people are viewing", "people viewing", "just bought", "others bought", "bought in the last", "trending now", "people have this in their cart", "viewed this today"],
    ),
    "manipulative_consent": PatternDefinition(
        key="manipulative_consent", name="Manipulative Consent Interface", category="ui_fairness", default_severity="Medium", penalty=8,
        reason="The consent dialog makes accepting far easier than declining.",
        explanation="Highlighted 'Accept all' buttons with hidden or greyed 'Reject' options steer you toward sharing more data than you intend.",
        recommendation="Look for 'Manage preferences' or 'Reject all' links, even if they are small or low-contrast.",
        keywords=["accept all", "agree and continue", "manage preferences", "i agree", "allow all cookies", "by continuing you agree"],
    ),
    "privacy_zuckering": PatternDefinition(
        key="privacy_zuckering", name="Privacy Dark Pattern", category="transparency", default_severity="Medium", penalty=8,
        reason="Users are nudged to share more personal data than necessary.",
        explanation="Requests for contacts, location or marketing consent framed as required, when they are optional, are a privacy dark pattern.",
        recommendation="Only grant permissions that are essential for the purchase. Look for 'skip' options.",
        keywords=["share your contacts", "allow location", "sign up for updates", "marketing emails", "share with partners", "opt in to"],
    ),
    "hidden_information": PatternDefinition(
        key="hidden_information", name="Hidden Information", category="transparency", default_severity="Medium", penalty=8,
        reason="Important terms are visually de-emphasised (tiny text, low contrast, collapsed sections).",
        explanation="Key conditions such as return policy, minimum term or fees are present but styled so you are unlikely to read them.",
        recommendation="Expand collapsed sections and read footnotes marked with * before committing.",
        keywords=["terms apply", "*conditions", "see details", "t&c apply", "restrictions apply", "subject to"],
    ),
}

SEVERITY_ORDER = {"High": 3, "Medium": 2, "Low": 1}

TRUST_CATEGORIES = {
    "transparency": "Transparency",
    "pricing_clarity": "Pricing Clarity",
    "ui_fairness": "UI Fairness",
    "checkout_transparency": "Checkout Transparency",
    "marketing_pressure": "Marketing Pressure",
}


def get_pattern(key: str) -> PatternDefinition:
    return PATTERNS[key]


def pattern_name(key: str) -> str:
    return PATTERNS[key].name if key in PATTERNS else key.replace("_", " ").title()
