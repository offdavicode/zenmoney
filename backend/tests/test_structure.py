from pathlib import Path


def test_expected_architecture_directories_exist() -> None:
    project_root = Path(__file__).resolve().parent.parent

    assert (project_root / "models").exists()
    assert (project_root / "schemas").exists()
    assert (project_root / "routers").exists()
    assert (project_root / "services").exists()
    assert (project_root / "utils").exists()
