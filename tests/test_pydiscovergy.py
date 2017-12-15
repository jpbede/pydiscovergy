from pydiscovergy import PyDiscovergy
import os

def test_login():
    """Tests an API call"""

    discovergy_instance = PyDiscovergy("pydiscovergy")
    result = discovergy_instance.login(os.environ['PYTEST_EMAIL'], os.environ['PYTEST_PASSWORD'])

    assert isinstance(discovergy_instance, PyDiscovergy)
    assert result == True