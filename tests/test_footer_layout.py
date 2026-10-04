"""Real widget geometry checks; do not load or save user settings."""
import sys

import pytest
import app


@pytest.mark.skipif(sys.platform != "win32", reason="Windows desktop layout")
def test_support_row_aligns_with_status(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "load_config", lambda: app.normalize_config({"output_dir": str(tmp_path)}))
    monkeypatch.setattr(app, "ensure_tools_or_exit", lambda root: None)
    monkeypatch.setattr(app.CleanConverter, "_start_startup_sequence", lambda self: None)
    app.ctk.set_widget_scaling(1.0)
    app.ctk.set_window_scaling(1.0)
    root = app.CleanConverter()
    try:
        root.deiconify()
        for width, height in [(740, 540), (1080, 860)]:
            root.geometry(f"{width}x{height}")
            root.update()
            hint, link, status, credit = root.support_hint, root.support_link, root.status, root.credit
            assert abs(hint.winfo_rootx() - status.winfo_rootx()) <= 1
            gap = link.winfo_rootx() - (hint.winfo_rootx() + hint.winfo_width())
            assert 0 <= gap <= 5
            assert link.winfo_rootx() + link.winfo_width() < credit.winfo_rootx()
            assert link.cget("text") == "demirdemiroz.com"
        assert app.BUG_REPORT_URL == "https://demirdemiroz.com/iletisim/"
        assert not hasattr(root, "report_bug_btn")
    finally:
        for identifier in root.tk.call("after", "info"):
            root.after_cancel(identifier)
        root.destroy()
