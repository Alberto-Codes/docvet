from __future__ import annotations

import docvet


def test_package_when_imported_has_main_attribute():
    assert hasattr(docvet, "main")


def test_main_when_accessed_is_callable():
    assert callable(docvet.main)


def test_main_when_called_outputs_greeting(capsys):
    docvet.main()
    captured = capsys.readouterr()
    assert "docvet" in captured.out.lower()
