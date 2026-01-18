try:
    import comtypes
    import pycaw
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
