# Configuration references

The standard run configuration is one self-contained YAML or JSON file containing
`catalog` and `request` sections. The reference below documents that format. Practical workflows and
input-generation scripts live only in [autostacgis-python examples](https://github.com/autostacgis/autostacgis-python/tree/main/examples).
They are maintained independently, rather than mirrored between repositories.

| Example | Coverage |
| --- | --- |
| [Configuration reference](configuration-reference/config.yaml) | Inline catalog and request; compact and full plugin declarations; settings schemas; catalog/request solver and runtime settings; local extension schemas; source and module selection; sequence routing; composed and per-input goals; typed transfer; checkpoints; per-output publication; named steps; native result links; metadata pointers; explicit output paths. |

The reference intentionally spells out many optional fields. Its numbers and paths
illustrate the format; they are not recommended defaults or a ready-to-run recipe.
For example, `query: {}` is a provider-defined object, and `discovery` can be set to
`true` to request planning without processing. `catalog.extension_schemas` registers
a local STAC schema. All ordinary paths resolve from the entry configuration's
folder.

Run `python tools/validate.py` to check the schemas, reference configurations, and
pinned extension hashes. See the [specification](../specification.md) for field
semantics and default behavior. Most fields can be omitted in a practical
configuration.
