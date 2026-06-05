# AI Browser Extension for Phishing Detection

## Introduction

Phishing websites imitate legitimate services to steal sensitive information such as passwords, account details, and payment data. This project builds an AI-powered browser extension that checks the current URL and warns the user if the website appears suspicious.

## Objectives

- Detect phishing URLs in real time.
- Train a machine learning model using URL-based features.
- Provide immediate warnings through a browser extension.
- Demonstrate the use of artificial intelligence in cybersecurity.

## Methodology

The system uses the public `ESDAUNG/PhishDataset` balanced dataset, collected from PhishTank and IP2Location-based legitimate sources. The dataset is normalized into `url,label` format before training, then augmented with a small trusted legitimate anchor set to reduce false positives on common services. The system extracts measurable URL features, sends them to a trained machine learning classifier, and returns a prediction of `legitimate` or `phishing`.

## System Architecture

1. Browser extension captures the current tab URL.
2. Flask backend receives the URL through `/predict`.
3. Feature extractor converts the URL into numeric features.
4. Trained model predicts the class and risk score.
5. Extension displays the result to the user.

## Model Training

The training script evaluates Logistic Regression, Decision Tree, Random Forest, and Naive Bayes. The final model is selected using phishing recall first because missing a phishing website is more dangerous than flagging an extra suspicious site. The current trained model is Random Forest, with 94.52% accuracy and 94.93% phishing recall on the held-out split.

The feature set includes URL length, punctuation counts, digit counts, HTTPS usage, IP address detection, subdomain count, suspicious keyword count, suspicious TLD detection, URL shortener detection, entropy, path depth, query length, encoded characters, executable file extensions, and brand impersonation indicators.

## Testing

Testing includes dataset validation, feature extraction tests, backend API tests, model metric evaluation, browser extension checks, and end-to-end testing from URL capture to warning display. Suspicious URLs trigger a full-page warning overlay with **Go Back** and **Continue Anyway** actions.

## Results

The model report is generated in `model/metrics.txt` after training. It includes accuracy, phishing recall, F1-score, confusion matrix, and classification report for each trained model.

## Limitations

The current implementation uses URL features only and requires a local Flask backend. It is suitable for academic demonstration and can be improved with larger datasets and webpage content analysis.

## Future Improvements

- Use a larger live phishing dataset.
- Add HTML, JavaScript, and page-text analysis.
- Add domain reputation and WHOIS features.
- Run prediction directly inside the extension.
- Add user-controlled allowlist and blocklist features.
