import os
import json
import hashlib

class SimpleDiskCache:
    def __init__(self, cache_dir='cache_dir'):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f'{key}.json')
    
    def lookup(self, key, llm_string=''):
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                print("[Using cached response]")
                return json.load(f)
        return None
    
    def update(self, key, value, llm_string=''):
        cache_path = self._get_cache_path(key)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(value, f, ensure_ascii=False) 