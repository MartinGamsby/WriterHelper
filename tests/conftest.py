import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from articles import ArticlesModel  # noqa: E402


# ========================================================================================
@pytest.fixture
def pair(tmp_path):
    """FR/EN ArticlesModel wired to temp posts folders and temp config INIs."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    for hl, site in (("fr", "https://example.com/fr/"), ("en", "https://example.com/en/")):
        posts = tmp_path / hl
        posts.mkdir()
        (cfg_dir / f"settings_{hl}.ini").write_text(
            "[Paths]\nposts = %s\n[URLs]\nwebsite = %s\n" % (str(posts), site))
    return ArticlesModel.create(config_dir=str(cfg_dir))


@pytest.fixture
def fr(pair):
    return pair.fr()
