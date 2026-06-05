from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.features import features_to_frame, normalize_url


ROOT_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT_DIR / "model" / "phishing_model.pkl"
TRUSTED_DOMAINS_PATH = ROOT_DIR / "dataset" / "trusted_legitimate_domains.csv"
USER_FEEDBACK_PATH = ROOT_DIR / "dataset" / "user_legitimate_feedback.csv"

app = Flask(__name__)
CORS(app)


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. Run python backend/train_model.py first."
        )
    return joblib.load(MODEL_PATH)


def load_trusted_domains():
    if not TRUSTED_DOMAINS_PATH.exists():
        return set()

    data = pd.read_csv(TRUSTED_DOMAINS_PATH)
    return {
        str(domain).strip().lower().strip(".")
        for domain in data.get("domain", [])
        if str(domain).strip()
    }


def is_trusted_domain(url):
    hostname = (urlparse(url).hostname or "").lower().strip(".")
    trusted_domains = load_trusted_domains()
    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in trusted_domains
    )


def append_unique_csv_row(path, columns, row, unique_column):
    path.parent.mkdir(exist_ok=True)

    if path.exists():
        data = pd.read_csv(path)
    else:
        data = pd.DataFrame(columns=columns)

    unique_value = row[unique_column]
    existing_values = set(data.get(unique_column, pd.Series(dtype=str)).astype(str))
    if unique_value not in existing_values:
        data = pd.concat([data, pd.DataFrame([row])], ignore_index=True)
        data.to_csv(path, index=False)


def trusted_domain_for_url(url):
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().strip(".")
    if not hostname:
        return ""
    parts = hostname.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/mark-legitimate")
def mark_legitimate():
    payload = request.get_json(silent=True) or {}
    url = normalize_url(payload.get("url", ""))

    if not url:
        return jsonify({"error": "url is required"}), 400

    domain = trusted_domain_for_url(url)
    if not domain:
        return jsonify({"error": "valid URL hostname is required"}), 400

    append_unique_csv_row(
        USER_FEEDBACK_PATH,
        ["url", "label", "domain"],
        {"url": url, "label": "legitimate", "domain": domain},
        "url",
    )
    append_unique_csv_row(
        TRUSTED_DOMAINS_PATH,
        ["domain"],
        {"domain": domain},
        "domain",
    )

    return jsonify(
        {
            "url": url,
            "domain": domain,
            "label": "legitimate",
            "message": "Website marked as legitimate.",
        }
    )


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    url = normalize_url(payload.get("url", ""))

    if not url:
        return jsonify({"error": "url is required"}), 400

    try:
        if is_trusted_domain(url):
            return jsonify(
                {
                    "url": url,
                    "prediction": "legitimate",
                    "risk_score": 0.01,
                    "source": "trusted_domain",
                }
            )

        model = load_model()
        features = features_to_frame(url)
        prediction = model.predict(features)[0]

        if hasattr(model, "predict_proba"):
            classes = list(model.classes_)
            phishing_index = classes.index("phishing")
            risk_score = float(model.predict_proba(features)[0][phishing_index])
        else:
            risk_score = 1.0 if prediction == "phishing" else 0.0

        return jsonify(
            {
                "url": url,
                "prediction": prediction,
                "risk_score": round(risk_score, 4),
            }
        )
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
