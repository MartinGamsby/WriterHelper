import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from articles import ArticlesModel  # noqa: E402
import browser_jobs  # noqa: E402
import publish_config  # noqa: E402


# ========================================================================================
@pytest.fixture(autouse=True)
def isolated_publish_state(tmp_path, monkeypatch):
    """Never read the developer's real settings_publish.ini or browser_jobs/ queue:
    point both at empty temp locations (defaults apply until a test writes them)."""
    monkeypatch.setattr(publish_config, "CONFIG_FILE",
                        str(tmp_path / "settings_publish.ini"))
    monkeypatch.setattr(browser_jobs, "JOBS_DIR", str(tmp_path / "browser_jobs"))


@pytest.fixture
def publish_ini(tmp_path):
    """Write the (isolated) settings_publish.ini: publish_ini("[Transport]\\nx = api")."""
    def write(text):
        (tmp_path / "settings_publish.ini").write_text(text, encoding="utf-8")
    return write


# ========================================================================================
@pytest.fixture
def pair(tmp_path):
    """FR/EN ArticlesModel wired to temp posts folders and temp config INIs."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    for hl, site in (("fr", "https://example.com/fr/blog/"),
                     ("en", "https://example.com/en/blog/")):
        posts = tmp_path / hl
        posts.mkdir()
        (cfg_dir / f"settings_{hl}.ini").write_text(
            "[Paths]\nposts = %s\n[URLs]\nwebsite = %s\n" % (str(posts), site))
    p = ArticlesModel.create(config_dir=str(cfg_dir))
    p.cfg_dir = str(cfg_dir)   # lets tests spin up a second, independent pair
    return p


@pytest.fixture
def fr(pair):
    return pair.fr()
