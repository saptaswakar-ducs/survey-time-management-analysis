"""Dependency-free runner (use `pytest` if you have it): python tests/run_tests.py"""
import sys, tempfile, pathlib, traceback, inspect, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).parent))


class _MP:
    def setattr(self, obj, name, val): setattr(obj, name, val)


fails = n = 0
for modname in ["test_data", "test_stats", "test_plots"]:
    mod = importlib.import_module(modname)
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if not name.startswith("test_"): continue
        n += 1
        kwargs = {}
        params = inspect.signature(fn).parameters
        if "tmp_path" in params: kwargs["tmp_path"] = pathlib.Path(tempfile.mkdtemp())
        if "monkeypatch" in params: kwargs["monkeypatch"] = _MP()
        try:
            fn(**kwargs); print("PASS", modname, name)
        except Exception:
            fails += 1; print("FAIL", modname, name); traceback.print_exc()
print(f"\n{n - fails}/{n} passed")
sys.exit(1 if fails else 0)
