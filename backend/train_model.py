from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from backend.features import features_to_frame, normalize_url


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "dataset" / "phishing_urls.csv"
TRUSTED_DOMAINS_PATH = ROOT_DIR / "dataset" / "trusted_legitimate_domains.csv"
USER_FEEDBACK_PATH = ROOT_DIR / "dataset" / "user_legitimate_feedback.csv"
MODEL_DIR = ROOT_DIR / "model"
REPORT_PATH = MODEL_DIR / "metrics.txt"
MODEL_PATH = MODEL_DIR / "phishing_model.pkl"


def load_dataset(path=DATASET_PATH):
    data = pd.read_csv(path)
    data.columns = [column.strip().lower() for column in data.columns]

    if "url" not in data.columns or "label" not in data.columns:
        raise ValueError("Dataset must contain url and label columns.")

    data = data[["url", "label"]].dropna()
    data["url"] = data["url"].map(normalize_url)
    data["label"] = data["label"].str.strip().str.lower()
    data = data[data["label"].isin(["phishing", "legitimate"])]
    data = data.drop_duplicates(subset=["url"])

    if USER_FEEDBACK_PATH.exists():
        feedback = pd.read_csv(USER_FEEDBACK_PATH)
        feedback.columns = [column.strip().lower() for column in feedback.columns]
        if "url" in feedback.columns:
            feedback = feedback[["url"]].dropna()
            feedback["url"] = feedback["url"].map(normalize_url)
            feedback["label"] = "legitimate"
            data = pd.concat([data, feedback], ignore_index=True)
            data = data.drop_duplicates(subset=["url"], keep="last")

    if TRUSTED_DOMAINS_PATH.exists():
        trusted_domains = pd.read_csv(TRUSTED_DOMAINS_PATH)
        trusted_domains["domain"] = trusted_domains["domain"].str.strip().str.lower()
        trusted_domains = trusted_domains.dropna().drop_duplicates()
        anchor_rows = []
        for domain in trusted_domains["domain"]:
            anchor_rows.extend(
                [
                    {"url": f"https://{domain}", "label": "legitimate"},
                    {"url": f"https://www.{domain}", "label": "legitimate"},
                    {"url": f"https://{domain}/login", "label": "legitimate"},
                    {"url": f"https://{domain}/account", "label": "legitimate"},
                ]
            )
        data = pd.concat([data, pd.DataFrame(anchor_rows)], ignore_index=True)
        data = data.drop_duplicates(subset=["url"])

    if data.empty:
        raise ValueError("Dataset has no valid rows after cleaning.")

    return data


def train():
    data = load_dataset()
    x = features_to_frame(data["url"].tolist())
    y = data["label"]

    stratify = y if y.value_counts().min() >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.3, random_state=42, stratify=stratify
    )

    models = {
        "Logistic Regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=3000)
        ),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Naive Bayes": GaussianNB(),
    }

    results = []
    best_name = None
    best_model = None
    best_score = (-1, -1)

    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        recall = recall_score(y_test, predictions, pos_label="phishing", zero_division=0)
        f1 = f1_score(y_test, predictions, pos_label="phishing", zero_division=0)
        accuracy = accuracy_score(y_test, predictions)
        results.append((name, accuracy, recall, f1, predictions))

        score = (recall, f1)
        if score > best_score:
            best_name = name
            best_model = model
            best_score = score

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)

    lines = [f"Best model: {best_name}", ""]
    for name, accuracy, recall, f1, predictions in results:
        lines.extend(
            [
                f"Model: {name}",
                f"Accuracy: {accuracy:.4f}",
                f"Phishing recall: {recall:.4f}",
                f"Phishing F1-score: {f1:.4f}",
                "Confusion matrix:",
                str(confusion_matrix(y_test, predictions, labels=["legitimate", "phishing"])),
                "Classification report:",
                classification_report(y_test, predictions, zero_division=0),
                "",
            ]
        )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {best_name} to {MODEL_PATH}")
    print(f"Saved metrics to {REPORT_PATH}")


if __name__ == "__main__":
    train()
