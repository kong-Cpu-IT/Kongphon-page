from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from joblib import dump

SAMPLES = [
    ("Government announces new education policy to improve schools", 0),
    ("Study finds that eating chocolate increases intelligence", 1),
    ("Local sports team wins championship after dramatic final", 0),
    ("Celebrity adopts alien baby, sources confirm", 1),
    ("New vaccine rollout begins in three cities this week", 0),
    ("Miracle cure for diabetes discovered in backyard garden", 1),
    ("Scientists publish reproducible results on climate study", 0),
    ("Secret ingredient makes you lose 20kg in 10 days", 1),
]


def train_and_save():
    texts = [t for t, _ in SAMPLES]
    labels = [l for _, l in SAMPLES]

    vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vec.fit_transform(texts)

    clf = LogisticRegression(max_iter=200)
    clf.fit(X, labels)

    dump(vec, "vectorizer.joblib")
    dump(clf, "model.joblib")
    print("Saved vectorizer.joblib and model.joblib")


if __name__ == "__main__":
    train_and_save()
