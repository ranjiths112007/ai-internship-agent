from __future__ import annotations

import re
from typing import Tuple


def inspect_page_safety(html_content: str, url: str = "") -> Tuple[bool, str, str]:
    """
    Inspects page HTML and URL for safety triggers.
    Returns (is_safe, reason, manual_action_instruction)
    """
    html_lower = html_content.lower()

    # 1. CAPTCHA & Bot Protection
    captcha_signals = [
        "g-recaptcha", "hcaptcha", "cf-turnstile", "cf-challenge",
        "captcha", "robotcheck", "security check", "verify you are human",
        "cloudflare-static", "ddos protection"
    ]
    for sig in captcha_signals:
        if sig in html_lower:
            return (
                False,
                f"CAPTCHA / Bot Protection detected ({sig}).",
                "MANUAL_ACTION_REQUIRED: Please open the application link directly in your browser and complete the security CAPTCHA verification."
            )

    # 2. OTP & 2FA Verification
    otp_signals = ["one-time password", "enter code sent to", "enter otp", "2fa", "two-factor authentication", "sms verification"]
    for sig in otp_signals:
        if sig in html_lower:
            return (
                False,
                f"Authentication / OTP challenge detected ({sig}).",
                "MANUAL_ACTION_REQUIRED: Please complete the 2FA / OTP phone verification in your browser."
            )

    # 3. Assessment & Coding Test
    assessment_signals = ["hackerrank", "codility", "testgorilla", "pymetric", "assess", "coding challenge", "personality test"]
    for sig in assessment_signals:
        if sig in html_lower or any(sig in url.lower() for sig in assessment_signals):
            return (
                False,
                f"Online assessment or test detected ({sig}).",
                "MANUAL_ACTION_REQUIRED: Please complete the technical/personality assessment directly on the portal."
            )

    # 4. Payment or Government ID
    sensitive_signals = ["credit card", "passport number", "social security number", "ssn", "national id", "pay application fee"]
    for sig in sensitive_signals:
        if sig in html_lower:
            return (
                False,
                f"Sensitive personal information / Payment field detected ({sig}).",
                "MANUAL_ACTION_REQUIRED: Please enter sensitive ID or payment details manually."
            )

    return (True, "Page is safe for automated form field pre-filling.", "")
