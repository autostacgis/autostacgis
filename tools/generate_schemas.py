"""Generate the JSON/YAML configuration contracts."""
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "schemas"
BASE = "https://autostacgis.github.io/autostacgis/v0.0.1/schemas/"


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


def save(name, schema):
    (ROOT / (name + ".json")).write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + name + ".json", **schema}, indent=2) + "\n")


string = {"type": "string", "minLength": 1}
strings = {"type": "array", "items": string, "uniqueItems": True}
mapping = {"type": "object"}
call = obj({"plugin": string, "settings": mapping}, ["plugin"])
transfer = {"enum": ["memory", "file", "optimized"]}
result = obj({
    "save": {"type": "boolean", "default": False, "description": "Save this result through its encoder and destination. Independent of the goal."},
    "encode": {"oneOf": [call, {"type": "null"}]},
    "data_out": call,
    "metadata_out": {"oneOf": [call, {"type": "array", "items": call}]},
    "filename_suffixes": {"type": "array", "items": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$"}, "description": "Append these filename tokens to this output asset's history."},
    "output_directory": {"oneOf": [string, obj({"jsonata": string}, ["jsonata"]), {"type": "null"}], "description": "Preferred Item output directory, set literally or from JSONata. Does not enable saving."},
    "transfer": transfer,
})
save("result", result)
execution = obj({"transfer": transfer, "checkpoint": {"oneOf": [call, {"type": "null"}]},
                 "outputs": {"type": "object", "additionalProperties": result}})
cap = obj({"implementation": string, "settings": mapping, "input_types": strings, "output_types": strings, "execution": execution, "contract": mapping}, ["implementation"])
capabilities = ["trigger", "metadata_in", "data_in", "sequence", "checks", "process", "encode", "data_out",
                "data_transfer", "checkpoint", "metadata_out", "goal", "solver", "services", "extensions"]
save("plugin", obj({"id": string, "requires": strings, "settings": mapping, "settings_schema": mapping,
    "capabilities": {**obj({c: cap for c in capabilities}), "minProperties": 1, "maxProperties": 1}}, ["id", "capabilities"]))
solver = call
save("catalog", obj({"version": {"const": "0.0.1"}, "plugins": {"type": "array", "items": {"oneOf": [
    {"$ref": BASE + "plugin.json"}, obj({"use": string, "settings": mapping, "execution": execution}, ["use"])]}},
    "defaults": {"type": "object", "properties": {"data_transfer": call}, "additionalProperties": False},
    "runtime": mapping, "solver": solver, "extension_schemas": {"type": "object", "additionalProperties": string}}, ["version", "plugins"]))
sequence_call = obj({"plugin": string, "settings": mapping, "scope": {"enum": ["inventory", "available"]}}, ["plugin"])
req = obj({"version": {"const": "0.0.1"}, "goal": {"$ref": BASE + "goal.json"}, "sources": strings,
           "query": mapping, "modules": strings, "module_settings": {"type": "object", "additionalProperties": mapping},
           "sequence": {"type": "object", "additionalProperties": {"oneOf": [sequence_call,
                {"type": "array", "minItems": 1, "items": sequence_call}, {"type": "null"}]}},
           "solver": solver, "runtime": mapping, "work_directory": string, "data_transfer": call,
           "checkpoint": {"oneOf": [call, {"type": "null"}]}, "discovery": {"type": "boolean"}}, ["goal"])
step = obj({"plugin": string, "settings": mapping,
    "sequence": {"type": "object", "additionalProperties": {"oneOf": [sequence_call,
        {"type": "array", "minItems": 1, "items": sequence_call}, {"type": "null"}]}}, "transfer": transfer, "checkpoint": {"oneOf": [call, {"type": "null"}]},
    "inputs": {"type": "object", "additionalProperties": {"type": "string", "pattern": "^result:"}},
    "outputs": {"type": "object", "additionalProperties": {"oneOf": [
        {"type": "string", "pattern": "^path:.+"}, result]}}}, ["plugin"])
step["patternProperties"] = {"^param:.+": {}}
req["properties"]["steps"] = {"type": "object", "minProperties": 1, "additionalProperties": {"oneOf": [step, obj({"auto": {"const": True}}, ["auto"])]}}
save("request", req)
structure = obj({"schemas": {"type": "array", "items": {"type": "string", "format": "uri"}, "uniqueItems": True},
                 "inline": mapping, "strict": {"type": "boolean", "default": True}})
groups = {c: {"type": "object", "additionalProperties": mapping} for c in capabilities}
groups["solver"].update(minProperties=1, maxProperties=1)
groups["trigger"]["maxProperties"] = 1
groups["goal"].update(minProperties=1, additionalProperties={"oneOf": [mapping, {"type": "array", "minItems": 1, "items": mapping}]})
orchestration = deepcopy(req)
orchestration["required"] = []
for name in ("version", "goal", "module_settings", "solver", "runtime"):
    orchestration["properties"].pop(name)
save("workflow", {"title": "Capability-grouped workflow", **obj({**groups, "metadata_structure": structure, "execution": orchestration}, ["solver", "goal"])})
save("config", {"oneOf": [{"$ref": BASE + "workflow.json"}, obj({"catalog": {"$ref": BASE + "catalog.json"}, "request": {"$ref": BASE + "request.json"}, "metadata_structure": structure}, ["request"])]})
save("goal", {"type": "object", "minProperties": 1})
