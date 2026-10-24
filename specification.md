# AutoSTACGIS 1.0

AutoSTACGIS synthesizes a workflow from candidate data, composable output goals, and available processing modules. The specification is independent of particular sensors, file formats, and pixel-processing libraries.

## Data objects

A data object binds one asset of a STAC Item to an immutable workflow identity. Its metadata is JSON. Native payload handles, acquisition state, selected asset name, source ancestry, and dependency ownership remain separate from STAC. An Item may describe several independently bound assets, including different data kinds.

Initial objects and predicted outputs have the same representation. A transformation creates new objects without changing its inputs. Output identity includes the module identity/version, settings, ordered named input identities, output port, and member index. Distinct operations must not be merged solely because their metadata is equal.

Data can be remote, local, or in memory. Discovery need not acquire payloads. Metadata plugins produce complete planning descriptions; discovery and any inspection are internal to the chosen plugin. EOReader inspects supported EO products; generic STAC readers handle arbitrary STAC documents. Discovery adapters can inspect local rasters, vectors, tables, and point clouds. Explicit kind configuration resolves formats with ambiguous contents.

Item location metadata may include `properties.data_state:directory_root`, the
deepest common parent directory of every asset href, including metadata and
previews. It is derived from asset locations rather than a product directory name.
A single asset yields its parent directory. Relative paths yield a relative root;
URI roots retain their scheme and authority, excluding queries and fragments.
Incompatible locations or an empty asset map yield null. Recompute the field when
asset locations change; it is not a base URI for resolving relative hrefs.

WorldView adapters may group matching local extracted MUL/PAN products into one
acquisition Item with separate imagery assets. Grouping preserves each component's
band, grid, calibration, and viewing metadata. It does not combine raster pixels.
A delivery containing multiple acquisitions must remain multiple Items.

## Workflow documents

Public workflow files use plugin types as top-level sections. Each section maps globally unique installed plugin IDs to parameter objects. `solver` contains exactly one plugin and `goal` at least one. A goal may map to an array of parameter objects for multiple conjunctive instances. `trigger` contains at most one plugin and defaults to immediate execution (`now`). Explicit parameters override plugin defaults. Shared runtime services and transfer dependencies need not be repeated in the document.

```json
{"solver":{"backward_chain":{}},"goal":{"metadata-value":{"path":"properties.ready","value":true}}}
```

`metadata_structure` stores shared STAC schema definitions. Optional `execution` holds orchestration fields such as explicit steps and discovery queries. Plugin settings belong to their capability sections. `schemas/workflow.json` describes the public format; `schemas/config.json` also accepts earlier catalog/request documents for compatibility.

Python plugin modules require a descriptive module docstring, unique ID, semantic VERSION, one CAPABILITY, IMPLEMENTATION, and REQUIRES. Optional literal DEFAULT_CONFIG contains capability-grouped supporting plugin parameters; referenced names become required dependencies. Explicit workflow values override these defaults. Descriptions, defaults, parameter types and parameter descriptions are exposed consistently to clients. Explicit JSON Schemas take priority over conservative reflection of simple annotated function parameters.

## One plugin system

A plugin has `id`, `requires`, optional settings and settings schema, and exactly one explicitly named capability in its `capabilities` object. The interfaces are:

| Capability | Responsibility |
| --- | --- |
| `trigger` | Start work from Python, CLI, scheduling, or another integration |
| `data_in` | Acquire or stage assets selected for execution |
| `metadata_in` | Discover inputs and produce STAC descriptions |
| `goal` | Build explicitly declared parameters for its required solver |
| `solver` | Synthesize workflows and validate outputs against its goal contract |
| `process` | Transform named input objects into named output objects |
| `sequence` | Split, select, regroup, and combine collections for processing |
| `checks` | Validate named inputs or their relationships |
| `encode` | Encode typed payloads into artifacts in a declared format |
| `data_out` | Save a supported typed artifact to a destination |
| `data_transfer` | Transfer typed payloads between plugins with memory/file policies |
| `checkpoint` | Save, find, validate, restore, and invalidate intermediate outputs |
| `metadata_out` | Save selected STAC metadata or return an updated Item |
| `services` | Provide shared workers, storage, logging, or other runtime resources |
| `extensions` | Provide scoped execution behavior |

A plugin must provide exactly one capability. Empty or multi-capability declarations are invalid. Python modules declare `CAPABILITY` as one interface name and `IMPLEMENTATION` as one callable; plural `IMPLEMENTATIONS` declarations are invalid. Shared libraries may back several separately named plugins. Standard plugins live in `autostacgis-plugins/plugins/autostacgis_plugins`, with one module per registration. Dependencies are explicit and scoped: a plugin cannot implicitly use a dependency of another plugin. Missing dependencies and dependency cycles are errors. An explicit `{plugin: ...}` binding in the invocation's configured settings authorizes calls to that selected plugin for that invocation, without granting its transitive dependencies. Execution order comes from data dependencies and requirements.

Catalogs select registered implementations with `plugins: [{use: name, settings: {...}}]` or explicit capability definitions. The Python registration namespace is the `autostacgis.plugins` entry-point group. Unselected external registrations must not be imported. Declared dependencies are loaded recursively. Compact settings configure the plugin's sole declared capability. A Python implementation may also be registered directly. A processing function exposes its complete contract beside its code, through a decorator or attached declaration.

## Goals

The `backward_chain` solver accepts four goal forms:

- `output`: constraints on a named result, optionally including kind, metadata predicates, count, source selection, and coverage.
- `for_each`: select initial objects and require a corresponding output for every selected member.
- `all_of`: all component goals must hold.
- `any_of`: at least one component goal must hold.

Repeated output names combine constraints on the same result. Different names may identify different results; results can share dependencies. Contradictory configuration for the same output is rejected. A `for_each` selection is fixed against the initial inventory and does not recursively include generated outputs. A collective mosaic cannot substitute for individually requested results.

Selectors can filter kind, metadata, bbox intersection, geometry intersection, and whether the native CRS is projected. Input selection is distinct from output requirements: selecting projected inputs excludes raw photographs, while requesting projected outputs allows suitable processing modules to derive them.

The `metadata-value` goal adapter targets `backward_chain` and requires an expected JSON `value` plus exactly one of a metadata `path` or a `jsonata` expression. Optional JSON `parameters` are available to the goal and source selection expressions. JSONata receives the Item, bound asset, asset key, kind, and parameters. `$intersects`, `$covers`, and `$within` accept GeoJSON or STAC bounding boxes, allowing AOI selection from `item.bbox`, `item.geometry`, or another geometry field. Selection filters discovered candidates; a source provider's query controls remote discovery. The adapter also supports named outputs, kinds, per-member goals, counts, coverage, and publication, as declared in its strict settings contract.

An output source `select` requires ancestry from every selected object. Without it, the planner may choose a useful subset of the candidate inventory. A `count` requires that many distinct output identities. Unknown metadata cannot satisfy a predicate.

A mosaic request declares a coverage requirement and a `data_state:mosaic` metadata predicate directly in its output goal. Geometry coverage means the output footprint covers the requested polygon. It does not prove valid or cloud-free pixel coverage. A valid-data coverage goal must identify a measured metadata geometry through `path`. Raw drone photographs with unknown footprints remain `geometry: null` and cannot prove coverage.

STAC Item geometry uses WGS84. Native raster CRS and grid metadata belong in the Projection extension. A geographic CRS is not a projected CRS; an RPC model or camera location is not an affine georeferenced grid. Vector and point-cloud descriptions do not require raster fields.

## Processing contracts

Every module declares named `argument_requirements`, `input_requirements`, `outputs`, optional `cost`, settings, and an implementation version.

An argument declaration specifies an optional data kind, `one` or `many` cardinality, metadata requirements, and optionally a selected asset, minimum member count, or grouping policy. Requirements can address Item properties, assets, and nested metadata. `$asset` denotes the bound asset. Python functions may accept named arguments plus settings/context, or a complete dictionary of input lists.

Cross-input requirements express relationships such as compatible acquisition, matching grids, overlap, or source membership. Checks reference input argument names. Pure Python predicates may implement custom checks; declarations should identify observed metadata paths when possible so backward relevance can be narrowed.

Requirements use conjunction, disjunction, negation, exact equality, membership, array membership, array-entry matching, or existence. Missing and null values are unknown; negation preserves unknown. Custom record predicates return true, false, or unknown. JSONata predicates receive `item`, `asset`, `asset_key`, `kind`, and explicit JSON `parameters`. With `equals`, an expression's result is compared with the expected JSON value; otherwise the expression must return a boolean. Booleans and numbers are distinct. Optional `observes` declares all metadata paths read; omission means all metadata. Spatial comparisons use the operands' shared coordinate system and return unknown for missing or invalid geometry. STAC bbox spatial tests support four or six numbers, ignore elevation, and handle west-greater-than-east boxes at the antimeridian.

Each input and output declares supported `data_types`, independently of its scientific kind. Every output must declare at least one type. Each output also declares a kind and a metadata construction policy. `inherit_metadata: []` starts empty; references such as `[image, reference.properties.platform]` copy complete objects or selected subtrees. Inheritance merges in order, with later values winning. Most raster-to-raster and vector-to-vector operations should copy metadata before editing it.

`set` assigns literal JSON at dotted paths, `append` extends arrays, and `remove` deletes paths. Each assignment is a single-entry object. Null means unknown. Dots and backslashes in keys are escaped. Metadata edits apply in the order inheritance, set, append, remove. An append can derive its value from settings through JSONata.

An output with `each_from` creates one object per member of that input. Otherwise it creates one object. Multi-output operations execute once. A `geometry: union` policy predicts combined extent when all contributing geometries are known. A pure prediction function may calculate additional metadata without executing pixel processing. Measured attributes remain unknown until execution.

Output effects are declarations, not inferred from the execution code. Native implementations must report actual results consistent with their contracts. Execution refreshes grid and geometry metadata from payloads, validates promised effects and histories, and rechecks final goals. Metadata validation does not by itself prove the scientific correctness of an algorithm.

## Sequence routing and collection barriers

Collection ports bind lists of ordinary data objects. Default grouping defines members from the initial inventory before processing-state requirements are checked. A suitable version of every member must be available before the operation can run. One version of each logical member is selected; its source and derivative are not treated as two independent observations.

Modules declare a `sequence` policy on collection inputs. Requests override `sequence["module.port"]` with one call or an ordered list of calls. Policies can split collections into independent batches, filter or group by metadata, or combine routed groups. The built-in `split` takes a positive `size`; `combine` joins groups without merging their files or pixels. Each policy must return nonempty groups of unique input identities; core rejects invented members. Groups govern real planner bindings, member barriers, dependencies, and execution cardinality. A named step may override a policy by input port under `steps.<name>.sequence`; separate occurrences of a processing plugin can therefore split and combine differently. A null override allows subset selection by the solver. An `available` grouping scope can include generated objects. Grouping creates bindings rather than artificial dataset objects. Group outputs can subsequently feed individual operations, and those results can be gathered again.

## Workflow synthesis and costs

The reference solver performs backward dataflow synthesis. For a required output state, it identifies declared producer effects and recursively derives their input requirements. It memoizes subproblems, prunes unreachable antecedents, reuses generated objects, and propagates selected input versions into auxiliary derivations such as footprints and masks. Processing functions do not execute during search. An explicitly required aggregation is constructed from members satisfying the other requested states.

If multiple loaded algorithms establish the same required state, synthesis raises `AmbiguousProducer` naming the requirement and plugins. The user must select one producer in the catalog. Carrying an already-required state through a transformation does not make it a competing producer. Distinct required effects, input bindings, and source versions remain separate planning decisions.

Costs default to one. A cost can be a constant, a JSONata expression over declared parameter paths and full input metadata/settings, or a pure Python function. Costs are evaluated against the selected versions of inputs. Array histories therefore affect downstream costs. Costs must be finite, deterministic, and nonnegative; time, randomness, and dynamic evaluation are unavailable to JSONata planning expressions.

An operation producing several outputs is charged once, including when outputs serve different goals. Shared upstream operations are likewise paid once. Costs guide the backward search's operation order; the solver evaluates previews of effects on downstream costs, then computes real costs against selected input metadata. It retains successful derivations rather than exhaustively enumerating permutations. The resulting status is `synthesized`, without a global minimum-cost guarantee. Hard precedence must follow from input requirements and output effects; cost preferences need not impose absolute precedence.

Search has explicit `max_steps`, `max_states` (memoized subproblems), `max_bindings`, and `timeout` limits. Resource exhaustion raises `SearchLimit`; an unsuccessful backward derivation raises `NoPlan`. These outcomes make no claim about all conceivable workflows outside the construction rules or bounds. Histories and declared cost-dependent metadata participate in derivation comparison; original source identities are preserved.

## Execution and payload exchange

A plan is a dependency DAG with named input/output identities, effective settings, costs, and predicted Items. A `metadata_in` provider implements `discover(settings, query, context)` and produces STAC-described records without acquiring remote imagery. EOReader performs filesystem product discovery internally; it does not require a separate glob plugin. A provider may additionally implement `discover_from(..., records)` for inventory-dependent metadata. A `data_in` provider implements `acquire(record, settings, context)` for selected assets. Discovery and acquisition are separate plugin registrations. A metadata provider may explicitly declare a `data_in` route to an acquisition dependency; the core records that route on discovered records. Scoped `context.acquirer(name)` access lets stateful adapters share a discovery/download session without granting another capability to either plugin. Core replans when acquisition updates the descriptions; there is no separate metadata-enrichment stage. Dataflow dependencies determine scheduling; independent nodes may run concurrently.

Raster payloads expose replayable windows backed by native buffers. Vector, table, and point-cloud payloads expose Arrow batches. Python orchestrates native numerical and geospatial operations. Files may be materialized through storage when an algorithm requires random access or memory limits require spilling. A streaming contract does not imply that every algorithm is single-pass.

Runtime services own global workers, thread budgets, tile sizes, memory budgets, scratch storage, logging, and scratch lifetimes. Nested parallelism uses scoped executors. Plugins must not create uncontrolled worker pools. Process transfer can use shared buffers or staged files. Lazy output lifetime is owned by the run result; explicit writers produce durable outputs.

Writers support data formats independently of STAC publication. Zarr can embed a STAC description. GeoTIFF/COG writers embed the complete Item as JSON in the `STAC` metadata tag and map compatible fields to native headers. Metadata writers publish ordinary STAC JSON or catalogs. Runtime handles must not be mistaken for durable URLs.

## Typed transfer and publication

The exchange types are `raster` (replayable native windows), `batches` (Arrow batches
for tables, vectors, or points), `bytes`, `byte-stream` (a factory returning a fresh
iterator of byte chunks), `path` (a file or directory), and `json`. Plugins may add
namespaced types with a matching transfer implementation. Scientific `kind` and
exchange type serve different purposes. Processing ports declare `data_types`;
encoders, destinations, and transfer implementations declare `input_types` and
`output_types`. Core validates actual values against these declarations and rejects
incompatible publication pipelines before execution when their types are known.

Every processing edge passes through the configured `data_transfer` provider.
`catalog.defaults.data_transfer` selects the default; `request.data_transfer` can
override it. The reference `buffered-transfer` implementation has a `memory_bytes`
setting. `transfer: memory`, `file`, or `optimized` can be declared on a process
contract, a named step, or a port. The default is `optimized`. Memory mode explicitly
requests buffering; file mode requests file backing. Optimized mode reserves a
shared run budget, keeps fitting native results or byte chunks in memory, and
spills larger values to window-readable files or replayable streams. This is a
budget for managed exchange buffers, not a bound on total process RSS or on memory
allocated internally by numerical libraries. Byte consumers must accept `path` or
`byte-stream` to permit spilling. Scratch remains valid while the run result is open.

Publication belongs to an output policy, declared by a processing plugin, overridden
under `steps.<name>.outputs.<port>.publish`, or attached to an `output`/`for_each`
goal. It uses the same registered capabilities for intermediate and final results:

```yaml
publish:
  encode: {plugin: geotiff}
  data_out:
    plugin: filesystem
    settings: {path: ./output/mosaic.tif}
  metadata_out: {plugin: stac-json}
```

An encoder is optional when a process already returns a destination-supported type.
GeoTIFF, COG, Zarr and Parquet are encoders; filesystem and S3 are destinations.
Filesystem accepts bytes, replayable byte streams, and file/directory paths, writes
atomically, and refuses existing outputs unless `overwrite` is enabled. Its default
is a unique path below `output/data`. The saved location replaces the selected asset
href. A format artifact may request a registered metadata writer to update embedded
metadata after its destination is known; core does not encode format-specific rules.

`metadata_out` returns an updated Item or null. `stac-item` updates an in-memory Item.
`stac-json` supports a full Item or a selected dotted `value_path`, an explicit `path`
or default directory, and an optional `href_field` to retain the saved reference in
the returned Item. Local JSON may also retain its own reference in the file. It delegates bytes to a `data_out` destination. Metadata APIs can receive
an Item directly without exposing a local filename. There is no separate delivery
stage in the request layout.

## Checkpoints

`request.checkpoint` selects a provider for all processing steps. Contracts and named
steps may override it; null disables it for that step. Checkpointing is opt-in. A
provider implements `save(key, outputs, inputs)` and `load(key, inputs)`. Save returns
a reference and durable output descriptions; load returns those typed output groups
or null. The reference file provider composes registered encoders, `data_out`, and
`checks`; encoders provide `restore(saved, record, settings)` and may declare their
`extension`, so the provider can reopen their results without assuming a format; it never treats a filename alone as evidence that an output is reusable.

A checkpoint identity includes implementation/dependency identity, effective
settings, input metadata, and actual input content. Completed manifests index named
outputs and their STAC Items, paths, types, and content checksums across runs. Files
are committed before a manifest becomes visible. Invalid or missing data, checksum
mismatches, or a configured check returning fail or unknown invalidate that entry;
its managed directory is removed and the processing step runs again. Providers
must confine deletion to their own checkpoint entry.

`file-checkpoint` supports `directory` relative to `config`, `cwd`, or `item` through
`relative_to`. Item mode reads `item_path`, defaulting to
`properties.data_state:directory_root`, and requires one known shared local root.
An absolute directory chooses a location directly. Its encoder map is keyed by
exchange type, and `checks` contains registered check calls. An optional check `inputs` map binds
check arguments to named saved output collections; otherwise all restored records
are supplied under `data`. Durable checkpoint
references remain separate from scientific STAC metadata in runtime state.

Processing functions can call `context.save_checkpoint(name, outputs)` and
`context.restore_checkpoint(name)`. Generators may yield `Checkpoint(name, outputs)`
events and then return their final named outputs. This permits partial progress to
be restored after interruption without making checkpoint storage part of the
numerical algorithm. Input dependencies and type/metadata contracts still apply.

## Serialization and validation

JSON is canonical for catalogs, goals, requests, and STAC metadata. YAML passes through the same converter and validation path. Duplicate keys, non-string keys, recursive structures, unsupported YAML values, and nonfinite numbers are errors. Python callbacks remain installed implementation code referenced by plugin identity.

Schemas in `schemas/` define the document interfaces. Pinned schemas in `extensions/` provide offline STAC extension validation. Implementations bundle a content-hashed specification snapshot. This specification and implementation use version `1.0.0`.

## Run configuration

Use the capability-grouped workflow format above for new configurations. The legacy reader also accepts one self-contained YAML or JSON file with
`catalog` and `request` sections. `catalog.plugins` selects
available capabilities independently of execution order. Omitting `catalog` uses
the installed default catalog. Omitting overrides retains plugin defaults. Existing
standalone catalog and request documents remain accepted for compatibility.
The solver seeks outputs satisfying `request.goal`, subject to plugin input/output
contracts, selected capabilities, and any explicit step constraints.

## Ordered overrides

An optional `request.steps` object contains unique step names in declaration order,
for JSON as well as YAML. Each processing step declares `plugin`, optional
`settings`, and optional `param:name` arguments. Parameters override step settings,
which override module settings and installed defaults. The availability list does
not establish execution order. A catalog processing entry may set `execution`
with default `transfer`, `checkpoint`, and output `publish` overrides, including
for automatically planned steps. These resource/output options are separate from
the numerical plugin `settings`. With no `steps`, ordinary goal synthesis is unchanged.

```yaml
steps:
  prepare: {auto: true}
  normalize:
    plugin: global_radiometric_match
    param:pif_method: entire
  finish: {auto: true}
```

`{auto: true}` opens only the gap in which it appears. The solver may insert the
prerequisites needed for the following explicit step, or derive remaining goals in
a trailing gap. A final gap before a strict suffix can establish goal states that
the suffix inherits. Explicit steps are mandatory even when the inventory already
satisfies the goal. Preceding stages complete before subsequent stages execute.
Without an automatic gap, a missing prerequisite or unsatisfied final goal is an
error. Ordinary contracts validate every binding; forced order never waives them.
A repeated plugin has independent settings at each named step. One-input steps bind
each eligible member; collection steps use declared grouping, with disjoint member
groups and larger groups preferred. Auxiliary inputs remain available for reuse.

`inputs: {image: 'result:previous:result'}` binds the native output port of a prior
named step. Core supplies omitted input bindings and intermediate payloads. A
parameter may read known Item metadata with
`param:crs: 'result:previous:result#/assets/data/proj:code'`. A metadata reference
requires one Item and a valid JSON Pointer; missing, forward, ambiguous, or
unpredicted values are errors. Execution checks that referenced metadata still
matches the planned value. Arbitrary runtime scalar return values are not an
additional namespace: processing outputs remain native records described by STAC.
There is no global constant scope or filename expression language.

`outputs: {result: 'path:./saved.tif'}` explicitly materializes a single output port.
Supported durable formats are GeoTIFF, Zarr, and Parquet for compatible data kinds.
The resulting asset `href` and native payload point to the saved product for
subsequent steps. An explicit path must identify exactly one Item, may not collide
with another output or overwrite an input, and is relative to the run configuration.
Unspecified outputs keep the ordinary in-memory/managed-storage behavior. `path:`
also resolves explicit path parameters, without filename transformations.


## Configuration imports

For configurations that need shared sections, optional substitution is available.
Most workflows should keep their configuration in one file.

Before schema validation or interpretation, JSON and YAML use the same `$import`
substitution. A directive at any depth selects a local file, optionally followed by
`#/a/JSON/pointer`. The selected value replaces the directive's containing object.
A whole object, array, or scalar may be selected. Object siblings recursively
override imported object fields; arrays and scalars replace rather than append.
A list of import paths merges objects from left to right before local overrides.
Paths resolve relative to the file containing the directive. Imported configuration
values are copied without rewriting ordinary paths; those remain relative to the
run configuration. Missing selections, recursive imports and incompatible merges
are errors. JSON Pointer escapes `~0` and `~1` select literal `~` and `/` in keys.

```yaml
catalog:
  $import: plugins.yaml#/catalog
request:
  goal:
    output:
      require:
        assets.$asset.data_state:mosaic: true
        assets.$asset.cf:standard_name: surface_bidirectional_reflectance
        assets.$asset.unit: "1"
  module_settings:
    atmospheric_correction:
      $import: defaults.json#/atmosphere
```

See the [import reference](examples/imports-reference/config.json) and its
[options fragment](examples/imports-reference/options.json) for JSON/YAML section
selection, scalar substitution, and local overrides. Import fragments are checked
through the resolved entry configuration by `tools/validate.py`.


## Solver plugins and contracts

A solver is a single-capability plugin, selected with `catalog.solver: {plugin: name, settings: {...}}`. Exactly one solver may be selected, including those loaded through dependencies. If none is selected, the Python implementation selects `backward_chain`. Request `solver` overrides must name that same solver and may change its settings.

Every solver implementation declares a JSON contract with `settings_schema`, optional default `settings`, and `goal_schema`. Settings schemas explicitly list properties and reject unknown parameters. `backward_chain` declares nonnegative integer `max_steps` (default 64), positive integer `max_states` and `max_bindings` (default 100000 each), and positive number `timeout` in seconds (default 120). It uses backward dataflow construction with memoization and metadata predicate regression; metadata goals are inputs to the algorithm. Other solvers may declare different goal parameters; the common goal schema accepts objects and the selected solver validates their structure.

Product states such as surface reflectance, normalization, registration, and mosaicking are metadata constraints in goal configuration. Generic goal adapters may construct solver-specific parameters. They declare `contract.solver` by its unique plugin ID, strict `contract.settings_schema`, and that same solver in `REQUIRES`. Missing solver dependencies, incompatible goals, two selected solvers, duplicate names, and undeclared nested dependencies are errors. Goal adapter output is validated against the selected solver's contract before planning.

All capabilities share `REQUIRES = ("unique-plugin-id", ...)`, serialized as `requires: [name, ...]`. Implementation dependencies cannot be removed by catalog configuration. Names are unique across capabilities; entry-point names must match implementation IDs. A solver factory receives `(application, prepared_request, settings)` and returns an object with `plan(records)` and `validate_outputs(plan, records)`. The executor uses that solver for actual and published goal validation.
