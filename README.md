# AI Browser Extension for Phishing Detection

This project detects suspicious phishing URLs with a machine learning model and warns users through a Chrome or Microsoft Edge extension.

## Project Structure

- `dataset/` contains the phishing URL dataset.
- `backend/` contains feature extraction, model training, and the Flask API.
- `model/` stores the trained model and metrics report.
- `extension/` contains the Manifest V3 browser extension.
- `tests/` contains automated Python tests.
- `docs/` contains report material.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `python` is not available, use `py` instead.

## Train the Model

```powershell
python -m backend.train_model
```

This trains Logistic Regression, Decision Tree, Random Forest, and Naive Bayes models. The script chooses the best model by phishing recall first and F1-score second.

Generated files:

- `model/phishing_model.pkl`
- `model/metrics.txt`

## Run the Flask Backend

```powershell
python -m backend.app
```

The API runs at:

```text
http://127.0.0.1:5000
```

Prediction endpoint:

```http
POST /predict
Content-Type: application/json

{
  "url": "https://example.com/login"
}
```

Example response:

```json
{
  "url": "https://example.com/login",
  "prediction": "legitimate",
  "risk_score": 0.12
}
```

## Load the Browser Extension

1. Open Chrome or Microsoft Edge.
2. Go to `chrome://extensions` or `edge://extensions`.
3. Enable Developer mode.
4. Click **Load unpacked**.
5. Select the `extension/` folder.
6. Start the Flask backend before browsing.

## Test the Project

```powershell
pytest
```

Manual tests:

- Visit safe sites such as `https://google.com`.
- Visit suspicious test URLs such as `http://192.168.10.25/login/verify-account`.
- Stop the backend and confirm the popup shows scanner unavailable.
- Use the popup rescan button on different tabs.

## Dataset Note

The project uses the public `ESDAUNG/PhishDataset` balanced dataset from GitHub, which contains URLs collected from PhishTank and legitimate URLs prepared from IP2Location-based sources. The original dataset uses `0 = legitimate` and `1 = phishing`; it is normalized into `dataset/phishing_urls.csv` with `url,label` columns. A small `dataset/trusted_legitimate_urls.csv` anchor set is added to reduce false positives on common trusted services.

Local dataset files:

- `dataset/real_phishdataset_balanced.xlsx`
- `dataset/phishing_urls.csv`
- `dataset/trusted_legitimate_urls.csv`

Current normalized dataset size: 20,077 unique URLs.

## Features

The model uses URL-only features including:

- Length, dot, hyphen, digit, and special-character counts
- HTTPS, IP address, `@`, encoded character, and redirect-like path flags
- Subdomain count, suspicious TLDs, URL shortener detection, and brand-in-subdomain signals
- URL/domain entropy, domain digit and hyphen counts, path depth, query length, and executable file indicators

## Limitations

- The first version uses URL-based features only.
- It does not inspect page content, certificates, screenshots, or live domain reputation.
- The browser extension depends on the local Flask backend.

## Future Improvements

- Train with a larger real-world dataset.
- Add webpage text and HTML feature extraction.
- Add domain age and WHOIS-based signals.
- Package the model for offline extension-side prediction.
- Add a user allowlist/blocklist.
  ###
