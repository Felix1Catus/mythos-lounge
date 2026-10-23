#!/usr/bin/env python3
"""capture_v3_fast — alias for capture_v3.py default mode (API-only interception).
Kept for muscle memory; all logic lives in capture_v3.py now. Usage identical."""
import os, sys
sys.argv = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "capture_v3.py")] + sys.argv[1:]
exec(open(sys.argv[0]).read())
