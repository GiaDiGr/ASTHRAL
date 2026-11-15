"""Public builds must not leak local interpreter artifacts or bootstrap source."""
import importlib.util
from pathlib import Path

def test_public_copy_excludes_python_cache_and_keeps_nested_runtime_bytes(tmp_path):
    script=Path(__file__).resolve().parents[2]/'web-local/build.py'
    spec=importlib.util.spec_from_file_location('browser_build_packaging_test',script)
    build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
    source=tmp_path/'src';source.mkdir();(source/'__pycache__').mkdir()
    (source/'__pycache__'/'local.cpython-313.pyc').write_bytes(b'machine-local')
    (source/'stale.pyc').write_bytes(b'cache');(source/'browser_bridge.py').write_bytes(b'bootstrap-only')
    (source/'runtime').mkdir();(source/'runtime'/'module.wasm').write_bytes(b'public-runtime-fixture')
    (source/'app.js').write_bytes(b'export const synthetic=true;')
    destination=tmp_path/'public';build.copy_public_source(source,destination)
    assert sorted(p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file())==['app.js','runtime/module.wasm']
    assert (destination/'runtime/module.wasm').read_bytes()==b'public-runtime-fixture'
