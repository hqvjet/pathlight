import os

def list_packages(root_dir="src"):
    for root, dirs, files in os.walk(root_dir):
        # package là folder có __init__.py
        if "__init__.py" in files:
            rel_path = os.path.relpath(root, root_dir)
            package = rel_path.replace(os.sep, ".")
            print("Package:", package)

        # file .py (module)
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                rel_path = os.path.relpath(os.path.join(root, f), root_dir)
                module = rel_path.replace(os.sep, ".")[:-3]
                print("Module:", module)

list_packages("src")
