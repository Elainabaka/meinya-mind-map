"""Paths that do not exist or lie outside the repo must fail loudly, not pass or scan the disk."""
from mindmap import cli as mindmap_cli


def test_check_missing_path_is_an_error(tmp_path, capsys):
    code = mindmap_cli.main(["check", str(tmp_path / "no-such-repo")])
    captured = capsys.readouterr()
    assert code == 2
    assert "no-such-repo" in captured.err
    assert "0 docs" not in captured.out


def test_claims_missing_doc_is_an_error_and_scans_nothing(tmp_path, capsys, monkeypatch):
    from mindmap import engine

    def boom(*args, **kwargs):
        raise AssertionError("must not scan a root for a doc that does not exist")
    monkeypatch.setattr(engine, "run", boom)
    code = mindmap_cli.main(["claims", str(tmp_path / "gone.md")])
    assert code == 2
    assert "gone.md" in capsys.readouterr().err


def test_claims_doc_outside_root_is_an_error(tmp_path, capsys):
    root = tmp_path / "repo"
    root.mkdir()
    doc = tmp_path / "other.md"
    doc.write_text("# x\n", encoding="utf-8")
    code = mindmap_cli.main(["claims", str(doc), "--root", str(root)])
    assert code == 2
    assert "other.md" in capsys.readouterr().err


def test_check_file_outside_root_is_an_error(tmp_path, capsys):
    root = tmp_path / "repo"
    root.mkdir()
    doc = tmp_path / "other.md"
    doc.write_text("# x\n", encoding="utf-8")
    code = mindmap_cli.main(["check", str(doc), "--root", str(root)])
    assert code == 2
    assert "other.md" in capsys.readouterr().err


def test_other_commands_reject_a_missing_folder(tmp_path, capsys):
    gone = str(tmp_path / "gone")
    for argv in (["cost", gone], ["context", "task", "--root", gone], ["impact", "--root", gone]):
        assert mindmap_cli.main(argv) == 2, argv
        assert "gone" in capsys.readouterr().err
