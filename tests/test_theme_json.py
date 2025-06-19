import json
import os


def test_fallback_theme_loads():
    path = os.path.join('src', 'fallback_theme.json')
    with open(path, 'r') as f:
        data = json.load(f)
    assert 'global' in data
