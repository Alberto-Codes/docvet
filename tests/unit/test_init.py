from __future__ import annotations

import docvet
from docvet import main


def test_package_importable():
    assert hasattr(docvet, "main")


def test_main_is_callable():
    assert callable(main)


def test_main_runs(capsys):
    main()
    captured = capsys.readouterr()
    assert "docvet" in captured.out.lower()
