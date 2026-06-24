from core.modifiers import ModifierSet, EMPTY

def test_empty_modifier_set():
    m = ModifierSet()
    assert m.is_empty()

def test_empty_constant_is_empty():
    assert EMPTY.is_empty()

def test_non_empty_when_wildcards():
    m = ModifierSet(wildcards=True)
    assert not m.is_empty()

def test_non_empty_when_timer():
    m = ModifierSet(decision_timer_seconds=3)
    assert not m.is_empty()
