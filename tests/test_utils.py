"Tests for utils module"
import pytest

from src.utils import milliseconds_to_string

@pytest.mark.utils
def test_milliseconds_to_string():
    """When not providing language, the time range should be returned in English."""
    
    assert milliseconds_to_string(900) == "1 seconds"
    assert milliseconds_to_string(31000) == "31 seconds"
    assert milliseconds_to_string(3571000) == "59 minutes 31 seconds"
    assert milliseconds_to_string(90061000) == "1 day 1 hour 1 minute 1 second"
    assert milliseconds_to_string(1781971000) == "20 days 14 hours 59 minutes 31 seconds"

@pytest.mark.utils
def test_milliseconds_to_string_cn():
    """When providing Chinese as the language, the time range should be returned in Chinese."""
    
    assert milliseconds_to_string(900, 'zh-CN') == "瞬时"
    assert milliseconds_to_string(31000, 'zh-CN') == "31秒"
    assert milliseconds_to_string(3571000, 'zh-CN') == "59分钟31秒"
    assert milliseconds_to_string(90061000, 'zh-CN') == "1天1小时1分钟1秒"
    assert milliseconds_to_string(1781971000, 'zh-CN') == "20天14小时59分钟31秒"