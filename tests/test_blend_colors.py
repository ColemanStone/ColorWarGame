import sys
import types

# Create stub modules for pygame and pygame_gui to avoid heavy dependencies
pygame_stub = types.ModuleType('pygame')
pygame_gui_stub = types.ModuleType('pygame_gui')
pygame_gui_core_stub = types.ModuleType('pygame_gui.core')
pygame_gui_elements_stub = types.ModuleType('pygame_gui.elements')

pygame_gui_core_stub.ObjectID = object  # minimal placeholder
pygame_gui_stub.UIManager = object      # minimal placeholder
pygame_gui_stub.core = pygame_gui_core_stub
pygame_gui_stub.elements = pygame_gui_elements_stub

sys.modules.setdefault('pygame', pygame_stub)
sys.modules.setdefault('pygame_gui', pygame_gui_stub)
sys.modules.setdefault('pygame_gui.core', pygame_gui_core_stub)
sys.modules.setdefault('pygame_gui.elements', pygame_gui_elements_stub)

sys.path.insert(0, 'src')
from ColorWarGame import AISim


def test_blend_colors(monkeypatch):
    # Bypass heavy initialization
    monkeypatch.setattr(AISim, '__init__', lambda self: None)

    assert AISim().blend_colors('#ff0000', '#00ff00') == '#7f7f00'
