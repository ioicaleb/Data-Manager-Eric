"""
cache_manager.py - Cloud-optimized In-Memory Cache Bridge

This module replaces disk-bound file storage with an active state memory proxy.
It mimics the signature of legacy file handlers, meaning your data_processor.py 
can continue calling read_json() and write_json() without throwing exceptions or errors.
"""

_global_db_cache = {}

def initialize_memory_cache(database_payload: dict):
    """
    Called by the Flet entry loading task. 
    Seeds your memory layers with structural records retrieved from PostgreSQL.
    """
    global _global_db_cache
    _global_db_cache = database_payload if database_payload else {}
    print(f"Memory Cache Proxy successfully initialized.")

def get_master_memory_payload() -> dict:
    """
    Returns the fully modified nested memory dictionary 
    to be committed directly into the PostgreSQL JSONB row.
    """
    global _global_db_cache
    return _global_db_cache

def read_json(filename):
    """
    Intercepts the legacy disk read and maps lookups straight to the cloud cache proxy.
    """
    global _global_db_cache
    
    if filename.startswith("precomputed_stats_"):
        player_name = filename.replace("precomputed_stats_", "")
        precomputed_section = _global_db_cache.get("precomputed_stats", {})
        return precomputed_section.get(player_name, None)
        
    if filename in _global_db_cache:
        return _global_db_cache[filename]
        
    print(f"Proxy Warning: Virtual data key '{filename}' not found in runtime memory.")
    return None

def write_json(filename, data):
    """
    Intercepts the legacy disk write and saves data modifications to memory.
    """
    global _global_db_cache
    
    if filename.startswith("precomputed_stats_"):
        player_name = filename.replace("precomputed_stats_", "")
        
        if "precomputed_stats" not in _global_db_cache:
            _global_db_cache["precomputed_stats"] = {}
            
        _global_db_cache["precomputed_stats"][player_name] = data
        return

    _global_db_cache[filename] = data