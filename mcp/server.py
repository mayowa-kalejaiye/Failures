"""Shim: delegates to mcp_server/server.py to avoid pip package shadowing."""
import pathlib, sys
# mcp_server is the real implementation (avoids name clash with pip 'mcp')
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import importlib.util, pathlib as _p
spec = importlib.util.spec_from_file_location("failures_mcp_server", str(_p.Path(__file__).parent.parent / "mcp_server" / "server.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
# re-export
mcp = mod.mcp
main = mod.main
if __name__ == "__main__":
    main()
