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
capabilities = ["trigger", "metadata_in", "data_in", "sequence", "checks", "process", "encode", "data_out",
                "data_transfer", "checkpoint", "metadata_out", "goal", "solver", "services", "extensions"]
sequence_call = obj({"plugin": string, "settings": mapping, "scope": {"enum": ["inventory", "available"]}}, ["plugin"])
req = obj({"sources": strings,
           "query": mapping, "modules": strings,
           "sequence": {"type": "object", "additionalProperties": {"oneOf": [sequence_call,
                {"type": "array", "minItems": 1, "items": sequence_call}, {"type": "null"}]}},
           "work_directory": string, "data_transfer": call,
           "checkpoint": {"oneOf": [call, {"type": "null"}]}, "discovery": {"type": "boolean"}})
step = obj({"plugin": string, "settings": mapping,
    "sequence": {"type": "object", "additionalProperties": {"oneOf": [sequence_call,
        {"type": "array", "minItems": 1, "items": sequence_call}, {"type": "null"}]}}, "transfer": transfer, "checkpoint": {"oneOf": [call, {"type": "null"}]},
    "inputs": {"type": "object", "additionalProperties": {"type": "string", "pattern": "^result:"}},
    "outputs": {"type": "object", "additionalProperties": result}}, ["plugin"])
step["patternProperties"] = {"^param:.+": {}}
req["properties"]["steps"] = {"type": "object", "minProperties": 1, "additionalProperties": {"oneOf": [step, obj({"auto": {"const": True}}, ["auto"])]}}
structure = obj({"schemas": {"type": "array", "items": {"type": "string", "format": "uri"}, "uniqueItems": True},
                 "inline": mapping, "strict": {"type": "boolean", "default": True}})
groups = {c: {"type": "object", "additionalProperties": mapping} for c in capabilities}
groups["solver"].update(minProperties=1, maxProperties=1)
groups["trigger"]["maxProperties"] = 1
groups["goal"].update(minProperties=1, additionalProperties={"oneOf": [mapping, {"type": "array", "minItems": 1, "items": mapping}]})
orchestration = deepcopy(req)
orchestration["required"] = []
save("workflow", {"title": "Capability-grouped workflow", **obj({**groups, "metadata_structure": structure, "execution": orchestration}, ["solver", "goal"])})
save("config", {"$ref": BASE + "workflow.json"})
for removed in ("catalog", "request", "plugin", "goal"):
    (ROOT / (removed + ".json")).unlink(missing_ok=True)
