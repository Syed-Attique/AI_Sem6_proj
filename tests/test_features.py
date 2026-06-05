from backend.features import extract_features, features_to_frame, normalize_url


def test_normalize_url_adds_scheme():
    assert normalize_url("example.com") == "http://example.com"


def test_extract_features_for_suspicious_url():
    features = extract_features("http://192.168.1.10/login/verify-account?id=123")

    assert features["has_ip_address"] == 1
    assert features["uses_https"] == 0
    assert features["suspicious_keyword_count"] >= 2
    assert features["query_param_count"] == 1
    assert features["has_repeated_digits"] == 1
    assert features["path_depth"] >= 1


def test_features_to_frame_uses_expected_columns():
    frame = features_to_frame(["https://google.com", "http://bank-update-login.test"])

    assert len(frame) == 2
    assert "url_length" in frame.columns
    assert "suspicious_keyword_count" in frame.columns
    assert "url_entropy" in frame.columns
    assert "has_suspicious_tld" in frame.columns
