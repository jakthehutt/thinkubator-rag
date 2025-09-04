from streamlit.testing.v1 import AppTest
import pytest
import os
from unittest.mock import patch

@pytest.fixture
def mock_env():
    """Fixture to mock the GEMINI_API_KEY environment variable."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "dummy_api_key"}):
        yield

def test_app_startup_and_components(mock_env):
    """
    Tests if the Streamlit app starts up without errors and if the main components are present.
    """
    at = AppTest.from_file("src/frontend/app.py")
    at.run()
    
    # Check if the title is correct
    assert at.title[0].value == "Thinkubator RAG Pipeline Explorer"
    
    # Check if the "Generate Answer" button is present
    assert len(at.button) > 0
    assert at.button[0].label == "Generate Answer"
    
    # Check for any exceptions
    assert not at.exception
