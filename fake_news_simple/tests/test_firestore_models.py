import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import User, AnalysisHistory


def test_model_classes_exist():
    assert User is not None
    assert AnalysisHistory is not None


def test_analysis_history_to_dict_contains_expected_fields():
    analysis = AnalysisHistory(
        user_id=1,
        title='Test title',
        content='Some content',
        prediction='Real',
        confidence=0.91,
    )
    payload = analysis.to_dict()
    assert payload['prediction'] == 'Real'
    assert payload['confidence'] == 0.91
    assert payload['title'] == 'Test title'
