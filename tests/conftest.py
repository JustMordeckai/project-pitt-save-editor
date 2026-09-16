import shutil
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def save_dir(tmp_path):
    """Throwaway copy of the game's save folder."""
    directory = tmp_path / "Project P.I.T.T"
    directory.mkdir()
    shutil.copy(FIXTURES / "savegame.save", directory / "savegame.save")
    shutil.copy(FIXTURES / "profile.cfg", directory / "profile.cfg")
    return directory
