# Simple Fake News Detection (toy)

Minimal example: a tiny TF-IDF + LogisticRegression model and a Flask UI.

Setup

1. Create and activate a virtualenv (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Train the toy model

```bash
python train_and_save.py
```

3. Run the web app

```bash
python app.py
```

Open http://127.0.0.1:5000 and test.

Note: This is a tiny demo with a handful of synthetic examples — not suitable for production.
# Fake News Demo (simple)

Minimal demo project: a small TF-IDF + LogisticRegression model and a Flask UI.

Usage

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r fake_news_simple/requirements.txt
```

2. Train model:

```bash
python fake_news_simple/train_model.py
```

3. Run the app:

```bash
python fake_news_simple/app.py
# then open http://127.0.0.1:5000
```
