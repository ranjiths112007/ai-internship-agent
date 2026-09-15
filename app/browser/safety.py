from __future__ import annotations

from typing import Tuple


CAPTCHA_SIGNALS = (
    "g-recaptcha", "hcaptcha", "cf-turnstile", "cf-challenge", "captcha",
    "robotcheck", "security check", "verify you are human", "cloudflare-static",
    "ddos protection", "checking your browser", "enable javascript and cookies",
)
AUTH_SIGNALS = (
    "one-time password", "enter code sent to", "enter otp", "2fa",
    "two-factor authentication", "sms verification", "sign in to apply",
    "log in to apply", "login to apply", "create an account to apply",
)
ASSESSMENT_SIGNALS = (
    "hackerrank", "codility", "testgorilla", "pymetric", "coding challenge",
    "technical assessment", "online assessment", "personality test", "take-home test",
)
SENSITIVE_SIGNALS = (
    "credit card", "debit card", "passport number", "social security number",
    "national id", "national identification", "pay application fee", "bank account number",
)


def _manual(reason: str, instruction: str) -> Tuple[bool, str, str]:
    return False, reason, f"MANUAL_ACTION_REQUIRED: {instruction}"


def inspect_page_safety(html_content: str, url: str = "") -> Tuple[bool, str, str]:
    """Classify a page before any automated application interaction.

    This function is deliberately conservative. A positive result means only that
    no known stop condition was detected; it never authorizes final submission.
    """
    html_lower = (html_content or "").lower()
    url_lower = (url or "").lower()

    for signal in CAPTCHA_SIGNALS:
        if signal in html_lower or signal in url_lower:
            return _manual(
                f"CAPTCHA / Bot Protection detected ({signal}).",
                "Complete the security challenge manually in your browser, then continue outside automation.",
            )

    for signal in AUTH_SIGNALS:
        if signal in html_lower or signal in url_lower:
            return _manual(
                f"Authentication / verification challenge detected ({signal}).",
                "Complete login, OTP, or account verification manually.",
            )

    for signal in ASSESSMENT_SIGNALS:
        if signal in html_lower or signal in url_lower:
            return _manual(
                f"Online assessment or test detected ({signal}).",
                "Complete the assessment manually. The agent will not automate tests or evaluations.",
            )

    for signal in SENSITIVE_SIGNALS:
        if signal in html_lower:
            return _manual(
                f"Sensitive personal or payment field detected ({signal}).",
                "Enter sensitive information manually and do not expose it to the agent.",
            )

    # Explicitly stop on final-submit language. Preparation may be safe, but the
    # agent must never interpret a normal submit button as permission to submit.
    return True, "No automated-stop condition detected; page may be inspected for safe form preparation.", ""
