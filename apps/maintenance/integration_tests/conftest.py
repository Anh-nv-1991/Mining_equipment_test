import sys
import os
import importlib

# Thêm thư mục gốc của project vào sys.path (thư mục chứa manage.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def pytest_configure(config):
    """
    Khi pytest khởi tạo, hãy kiểm tra và chuyển đổi tên module
    từ 'backend.apps.maintenance' sang 'apps.maintenance' để khớp với INSTALLED_APPS.
    """
    try:
        # Import module backend.apps.maintenance
        mod = importlib.import_module("backend.apps.maintenance")
        # Gán module này với tên mới "apps.maintenance"
        sys.modules["apps.maintenance"] = mod
    except Exception as e:
        print("Error in reassigning module name:", e)
