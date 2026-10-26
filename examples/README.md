# Configuration references

A workflow is one JSON or YAML file with plugin types as top-level sections. Each plugin name maps directly to its parameters. Only `solver` and `goal` are required. No catalog/request format or separate request file is accepted.

| Example | Coverage |
| --- | --- |
| [Configuration reference](configuration-reference/config.yaml) | Solver and goal parameters, plugin defaults, services, source queries, input grouping, transfers, checkpoints, named result saving, explicit steps, native result links, and metadata pointers. |
| [Imports](imports-reference/config.json) | Share grouped sections and select values with local JSON Pointers. |

The reference spells out optional fields for illustration. Its paths and numbers are not a ready-to-run recipe. Ordinary paths resolve from the entry configuration's folder. Practical workflows and demo input generation live in [autostacgis-python](https://github.com/autostacgis/autostacgis-python/tree/main/examples).

Run `python tools/validate.py` to check all schemas and reference examples. See the [specification](../specification.md) for field semantics.
