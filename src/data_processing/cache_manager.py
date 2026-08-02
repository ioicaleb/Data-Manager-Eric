"""
cache_manager.py - Cloud-optimized In-Memory Cache Bridge

This module replaces disk-bound file storage with an active state memory proxy.
It mimics the signature of legacy file handlers, meaning your data_processor.py 
can continue calling get_from_db() and send_to_db() without throwing exceptions or errors.
"""

_global_db_cache = {}

def initialize_memory_cache(database_payload: dict):
    """
    Called by the Flet entry loading task. 
    Seeds your memory layers with structural records retrieved from PostgreSQL.
    """
    global _global_db_cache
    if _global_db_cache.get("l_id") != database_payload.get("l_id"):
        _global_db_cache = database_payload if database_payload else {}
        print(f"Memory Cache Proxy successfully initialized.")

def get_master_memory_payload() -> dict:
    """
    Returns the fully modified nested memory dictionary 
    to be committed directly into the PostgreSQL JSONB row.
    """
    global _global_db_cache
    return _global_db_cache

def get_from_db(filename):
    global _global_db_cache
            
    if filename in _global_db_cache:
        return _global_db_cache[filename]
    return None

def send_to_db(filename, data):
    global _global_db_cache
    if "[Left the league]" not in filename:
        _global_db_cache[filename] = data