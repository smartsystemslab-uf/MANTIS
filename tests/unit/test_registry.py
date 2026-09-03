import pytest
from mantis.core.registry import Registry

def test_registry_basic_operations():
    r = Registry("TestReg")
    
    # Test registration
    r.register("key1", "val1")
    assert r.get("key1") == "val1"
    
    # Test duplicate registration
    with pytest.raises(ValueError):
        r.register("key1", "val2")
        
    # Test unknown key
    with pytest.raises(KeyError):
        r.get("unknown_key")
        
    # Test all
    r.register("key2", "val2")
    all_items = r.all()
    assert all_items == {"key1": "val1", "key2": "val2"}
    assert len(all_items) == 2
