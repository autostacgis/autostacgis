"""Validate local schemas and canonical JSON/YAML examples without network access."""
import hashlib
import json
from pathlib import Path
import yaml
from jsonschema import Draft7Validator, Draft202012Validator
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
schemas=[json.loads(path.read_text()) for path in [*ROOT.glob('schemas/*.json'),*ROOT.glob('extensions/*/schema.json')]]
registry=Registry().with_resources((schema['$id'],Resource.from_contents(schema)) for schema in schemas)
for schema in schemas:
    (Draft7Validator if 'draft-07' in schema['$schema'] else Draft202012Validator).check_schema(schema)
def merge(left, right):
    result = dict(left)
    for key, value in right.items():
        result[key] = merge(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict) else value
    return result

def read(path, active=()):
    path = path.resolve()
    assert path not in active, f"Recursive import: {path}"
    raw = json.loads(path.read_text()) if path.suffix == '.json' else yaml.safe_load(path.read_text())
    def expand(value):
        if isinstance(value, list):
            return [expand(v) for v in value]
        if not isinstance(value, dict):
            return value
        local = {k: expand(v) for k, v in value.items() if k != '$import'}
        if '$import' not in value:
            return local
        refs = value['$import']
        refs = refs if isinstance(refs, list) else [refs]
        selected = None
        for ref in refs:
            filename, _, pointer = ref.partition('#')
            imported = read(path.parent / filename, (*active, path))
            if pointer:
                assert pointer.startswith('/')
                for key in pointer[1:].split('/'):
                    key = key.replace('~1', '/').replace('~0', '~')
                    imported = imported[int(key)] if isinstance(imported, list) else imported[key]
            selected = imported if selected is None else merge(selected, imported)
        return merge(selected, local) if local else selected
    return expand(raw)

for path in sorted([*(ROOT/'examples').rglob('*.yaml'), *(ROOT/'examples').rglob('*.json')]):
    kind=path.stem
    if not (ROOT/f'schemas/{kind}.json').exists():
        continue  # Import fragments are checked through their resolved entry points.
    data=read(path)
    json_path=path.with_suffix('.json')
    if json_path.exists():
        assert data==read(json_path), path
    Draft202012Validator(json.loads((ROOT/f'schemas/{kind}.json').read_text()),registry=registry).validate(data)
print('Schemas and examples valid')

for name, entry in json.loads((ROOT/'extensions/lock.json').read_text()).items():
    assert hashlib.sha256((ROOT/f'extensions/{name}/schema.json').read_bytes()).hexdigest() == entry['sha256'], name
print('Pinned STAC extension schemas verified')
