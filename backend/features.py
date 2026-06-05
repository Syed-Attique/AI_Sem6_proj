import ipaddress
import math
import re
from urllib.parse import parse_qs, urlparse

import pandas as pd


SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "secure",
    "bank",
    "update",
    "account",
    "password",
    "billing",
    "confirm",
    "token",
    "signin",
    "wallet",
    "invoice",
    "limited",
    "locked",
    "suspend",
    "urgent",
]

SUSPICIOUS_TLDS = {
    "buzz",
    "cf",
    "click",
    "cn",
    "gq",
    "info",
    "live",
    "ml",
    "net",
    "online",
    "ru",
    "tk",
    "top",
    "work",
    "xyz",
}

SHORTENER_DOMAINS = {
    "bit.ly",
    "cutt.ly",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "rebrand.ly",
    "s.id",
    "t.co",
    "tiny.cc",
    "tinyurl.com",
}

KNOWN_BRANDS = {
    "adobe",
    "amazon",
    "apple",
    "bank",
    "binance",
    "chase",
    "coinbase",
    "discord",
    "dropbox",
    "facebook",
    "github",
    "google",
    "icloud",
    "instagram",
    "microsoft",
    "netflix",
    "office",
    "outlook",
    "paypal",
    "steam",
    "telegram",
    "twitter",
    "visa",
    "whatsapp",
}

FEATURE_NAMES = [
    "url_length",
    "dot_count",
    "hyphen_count",
    "digit_count",
    "has_at_symbol",
    "has_ip_address",
    "uses_https",
    "subdomain_count",
    "suspicious_keyword_count",
    "domain_length",
    "path_length",
    "query_param_count",
    "special_char_count",
    "special_char_ratio",
    "url_entropy",
    "domain_entropy",
    "domain_digit_count",
    "domain_hyphen_count",
    "path_depth",
    "has_suspicious_tld",
    "has_url_shortener",
    "has_repeated_digits",
    "brand_keyword_count",
    "brand_in_subdomain",
    "longest_token_length",
    "has_executable_file",
    "has_encoded_chars",
    "has_double_slash_redirect",
    "query_length",
    "url_to_domain_length_ratio",
]


def normalize_url(url):
    if not isinstance(url, str):
        return ""
    url = url.strip()
    if url and "://" not in url:
        url = f"http://{url}"
    return url


def _hostname(parsed_url):
    return parsed_url.hostname or ""


def _has_ip_address(hostname):
    if not hostname:
        return 0
    try:
        ipaddress.ip_address(hostname)
        return 1
    except ValueError:
        return 0


def _subdomain_count(hostname):
    if not hostname:
        return 0
    parts = hostname.split(".")
    if len(parts) <= 2:
        return 0
    return len(parts) - 2


def _tld(hostname):
    if "." not in hostname:
        return ""
    return hostname.rsplit(".", 1)[-1].lower()


def _subdomain(hostname):
    parts = hostname.split(".")
    if len(parts) <= 2:
        return ""
    return ".".join(parts[:-2])


def _entropy(value):
    if not value:
        return 0.0

    length = len(value)
    counts = {}
    for character in value:
        counts[character] = counts.get(character, 0) + 1

    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _path_depth(path):
    if not path or path == "/":
        return 0
    return len([part for part in path.split("/") if part])


def _longest_token_length(value):
    tokens = re.split(r"[^A-Za-z0-9]+", value)
    return max((len(token) for token in tokens), default=0)


def extract_features(url):
    normalized_url = normalize_url(url)
    parsed = urlparse(normalized_url)
    hostname = _hostname(parsed)
    lowered_url = normalized_url.lower()
    lowered_host = hostname.lower()
    path = parsed.path or ""
    query = parsed.query or ""
    special_char_count = len(re.findall(r"[^A-Za-z0-9]", normalized_url))
    brand_keyword_count = sum(1 for brand in KNOWN_BRANDS if brand in lowered_url)

    return {
        "url_length": len(normalized_url),
        "dot_count": normalized_url.count("."),
        "hyphen_count": normalized_url.count("-"),
        "digit_count": len(re.findall(r"\d", normalized_url)),
        "has_at_symbol": int("@" in normalized_url),
        "has_ip_address": _has_ip_address(hostname),
        "uses_https": int(parsed.scheme == "https"),
        "subdomain_count": _subdomain_count(hostname),
        "suspicious_keyword_count": sum(
            1 for keyword in SUSPICIOUS_KEYWORDS if keyword in lowered_url
        ),
        "domain_length": len(hostname),
        "path_length": len(path),
        "query_param_count": len(parse_qs(query)),
        "special_char_count": special_char_count,
        "special_char_ratio": special_char_count / max(len(normalized_url), 1),
        "url_entropy": _entropy(lowered_url),
        "domain_entropy": _entropy(lowered_host),
        "domain_digit_count": len(re.findall(r"\d", hostname)),
        "domain_hyphen_count": hostname.count("-"),
        "path_depth": _path_depth(path),
        "has_suspicious_tld": int(_tld(hostname) in SUSPICIOUS_TLDS),
        "has_url_shortener": int(lowered_host in SHORTENER_DOMAINS),
        "has_repeated_digits": int(bool(re.search(r"\d{3,}", normalized_url))),
        "brand_keyword_count": brand_keyword_count,
        "brand_in_subdomain": int(any(brand in _subdomain(lowered_host) for brand in KNOWN_BRANDS)),
        "longest_token_length": _longest_token_length(normalized_url),
        "has_executable_file": int(bool(re.search(r"\.(php|exe|scr|apk|zip|rar)(\?|$)", lowered_url))),
        "has_encoded_chars": int("%" in normalized_url),
        "has_double_slash_redirect": int("//" in path),
        "query_length": len(query),
        "url_to_domain_length_ratio": len(normalized_url) / max(len(hostname), 1),
    }


def features_to_frame(urls):
    if isinstance(urls, str):
        urls = [urls]
    rows = [extract_features(url) for url in urls]
    return pd.DataFrame(rows, columns=FEATURE_NAMES)
