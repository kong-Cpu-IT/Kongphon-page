import os
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - optional dependency for tests
    firebase_admin = None
    credentials = None
    firestore = None


_FALLBACK_STORE = {}
_FIRESTORE_ERROR = None

def _initialize_firestore():
    global db, _FIRESTORE_ERROR
    if firebase_admin is None or firestore is None:
        _FIRESTORE_ERROR = 'firebase-admin is not installed'
        return None

    if firebase_admin._apps:
        db = firestore.client()
        return db

    credential_path = os.getenv('FIRESTORE_CREDENTIALS') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credential_path:
        base_dir = os.path.dirname(__file__)
        for candidate in [
            os.path.join(base_dir, 'serviceAccountKey.json'),
            os.path.join(base_dir, '..', 'serviceAccountKey.json'),
            os.path.join(os.getcwd(), 'serviceAccountKey.json'),
        ]:
            if os.path.exists(candidate):
                credential_path = candidate
                break

    try:
        if credential_path and os.path.exists(credential_path):
            firebase_admin.initialize_app(credentials.Certificate(credential_path))
        else:
            firebase_admin.initialize_app()
        db = firestore.client()
        return db
    except Exception as exc:  # pragma: no cover - depends on environment
        _FIRESTORE_ERROR = str(exc)
        return None


db = _initialize_firestore()


def _collection(name):
    if db is not None:
        return db.collection(name)
    return None


def _fallback_collection(name):
    if name not in _FALLBACK_STORE:
        _FALLBACK_STORE[name] = {}
    return _FALLBACK_STORE[name]


class User(UserMixin):
    def __init__(self, username='', email='', password_hash=None, created_at=None, id=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at or datetime.utcnow()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        payload = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
        }
        if self.id:
            payload['id'] = self.id
        return payload

    def save(self):
        collection = _collection('users')
        if collection is not None:
            if self.id:
                collection.document(self.id).set(self.to_dict(), merge=True)
            else:
                doc_ref = collection.document()
                self.id = doc_ref.id
                doc_ref.set(self.to_dict())
            return True

        fallback = _fallback_collection('users')
        if self.id is None:
            self.id = str(len(fallback) + 1)
        fallback[self.id] = self.to_dict()
        return True

    @classmethod
    def find_by_username(cls, username):
        collection = _collection('users')
        if collection is not None:
            docs = collection.where('username', '==', username).limit(1).get()
            if docs:
                return cls.from_dict(docs[0])
            return None

        fallback = _fallback_collection('users')
        for item in fallback.values():
            if item.get('username') == username:
                return cls.from_dict(item)
        return None

    @classmethod
    def find_by_email(cls, email):
        collection = _collection('users')
        if collection is not None:
            docs = collection.where('email', '==', email).limit(1).get()
            if docs:
                return cls.from_dict(docs[0])
            return None

        fallback = _fallback_collection('users')
        for item in fallback.values():
            if item.get('email') == email:
                return cls.from_dict(item)
        return None

    @classmethod
    def get_by_id(cls, user_id):
        if not user_id:
            return None
        collection = _collection('users')
        if collection is not None:
            doc = collection.document(str(user_id)).get()
            if doc.exists:
                return cls.from_dict(doc)
            return None

        fallback = _fallback_collection('users')
        item = fallback.get(str(user_id))
        if item:
            return cls.from_dict(item)
        return None

    @classmethod
    def from_dict(cls, data):
        if hasattr(data, 'to_dict') and not hasattr(data, 'id'):
            data = data.to_dict()
        if not data:
            return None
        document_id = getattr(data, 'id', None)
        created_at = data.get('created_at') if isinstance(data, dict) else None
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            id=str(document_id or (data.get('id') if isinstance(data, dict) else '') or data.get('doc_id', '') or ''),
            username=data.get('username', '') if isinstance(data, dict) else '',
            email=data.get('email', '') if isinstance(data, dict) else '',
            password_hash=data.get('password_hash', '') if isinstance(data, dict) else '',
            created_at=created_at,
        )


class AnalysisHistory:
    def __init__(self, user_id=None, title='', content='', prediction='', confidence=0.0, created_at=None, id=None):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.prediction = prediction
        self.confidence = confidence
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'created_at': self.created_at,
        }

    def save(self):
        collection = _collection('analysis_history')
        if collection is not None:
            if self.id:
                collection.document(self.id).set(self.to_dict(), merge=True)
            else:
                doc_ref = collection.document()
                self.id = doc_ref.id
                doc_ref.set(self.to_dict())
            return True

        fallback = _fallback_collection('analysis_history')
        if self.id is None:
            self.id = str(len(fallback) + 1)
        fallback[self.id] = self.to_dict()
        return True

    @classmethod
    def get_by_id(cls, analysis_id):
        if not analysis_id:
            return None
        collection = _collection('analysis_history')
        if collection is not None:
            doc = collection.document(str(analysis_id)).get()
            if doc.exists:
                return cls.from_dict(doc)
            return None

        fallback = _fallback_collection('analysis_history')
        item = fallback.get(str(analysis_id))
        if item:
            return cls.from_dict(item)
        return None

    def delete(self):
        collection = _collection('analysis_history')
        if collection is not None and self.id:
            collection.document(self.id).delete()
            return True

        fallback = _fallback_collection('analysis_history')
        if self.id and self.id in fallback:
            del fallback[self.id]
            return True
        return False

    @classmethod
    def get_user_analyses(cls, user_id, limit=10, offset=0):
        collection = _collection('analysis_history')
        if collection is not None:
            docs = collection.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).offset(offset).limit(limit).get()
            return [cls.from_dict(doc) for doc in docs]

        fallback = _fallback_collection('analysis_history')
        items = [item for item in fallback.values() if item.get('user_id') == user_id]
        items.sort(key=lambda item: item.get('created_at', datetime.utcnow()), reverse=True)
        return [cls.from_dict(item) for item in items[offset:offset + limit]]

    @classmethod
    def count_user_analyses(cls, user_id):
        return len(cls.get_user_analyses(user_id, limit=100000, offset=0))

    @classmethod
    def count_by_prediction(cls, user_id, prediction):
        return sum(1 for item in cls.get_user_analyses(user_id, limit=100000, offset=0) if item.prediction == prediction)

    @classmethod
    def get_daily_stats(cls, user_id):
        stats = {}
        for item in cls.get_user_analyses(user_id, limit=100000, offset=0):
            day = item.created_at.strftime('%Y-%m-%d')
            stats[day] = stats.get(day, 0) + 1
        return stats

    @classmethod
    def from_dict(cls, data):
        if hasattr(data, 'to_dict') and not hasattr(data, 'id'):
            data = data.to_dict()
        if not data:
            return None
        document_id = getattr(data, 'id', None)
        created_at = data.get('created_at') if isinstance(data, dict) else None
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return cls(
            id=str(document_id or (data.get('id') if isinstance(data, dict) else '') or data.get('doc_id', '') or ''),
            user_id=data.get('user_id') if isinstance(data, dict) else None,
            title=data.get('title', '') if isinstance(data, dict) else '',
            content=data.get('content', '') if isinstance(data, dict) else '',
            prediction=data.get('prediction', '') if isinstance(data, dict) else '',
            confidence=data.get('confidence', 0.0) if isinstance(data, dict) else 0.0,
            created_at=created_at,
        )
