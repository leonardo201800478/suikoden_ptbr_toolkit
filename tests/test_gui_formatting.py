from suikoden_tool.gui import TranslationApp


def test_line_break_marker_is_rendered_as_newline_and_restored():
    source = "Line one∠Line two∠Line three"
    displayed = TranslationApp._markers_to_lines(source)

    assert displayed == "Line one\nLine two\nLine three"
    assert TranslationApp._lines_to_markers(displayed) == source


def test_line_break_conversion_normalizes_windows_newlines():
    assert TranslationApp._lines_to_markers("Linha 1\r\nLinha 2") == "Linha 1∠Linha 2"
