#!/usr/bin/env python3
"""
Check which routes are registered in the Flask app
"""
from app import app

print("Registered routes:")
print("="*60)
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"{methods:20} {rule}")
print("="*60)
print(f"Total routes: {len(list(app.url_map.iter_rules()))}")
