"""Generate the JSON/YAML configuration contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "schemas"
BASE = "https://autostacgis.github.io/autostacgis/v1.0.0/schemas/"


def obj(properties, required=()):
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


def save(name, schema):
    (ROOT / (name + ".json")).write_text(json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + name + ".json", **schema}, indent=2) + "\n")


string = {"type": "string", "minLength": 1}
strings = {"type": "array", "items": string, "uniqueItems": True}
mapping = {"type": "object"}
call = obj({"plugin": string, "settings": mapping}, ["plugin"])
publish = obj({"encode": call, "data_out": call, "metadata_out": {"oneOf": [call, {"type": "array", "items": call}]}})
transfer = {"enum": ["memory", "file", "optimized"]}
execution = obj({"transfer": transfer, "checkpoint": {"oneOf": [call, {"type": "null"}]},
                 "outputs": {"type": "object", "additionalProperties": obj({"publish": publish, "transfer": transfer})}})
cap = obj({"implementation": string, "settings": mapping, "input_types": strings, "output_types": strings, "execution": execution, "contract": mapping}, ["implementation"])
capabilities = ["trigger", "metadata_in", "data_in", "sequence", "checks", "process", "encode", "data_out",
                "data_transfer", "checkpoint", "metadata_out", "goal", "solver", "services", "extensions"]
save("plugin", obj({"id": string, "requires": strings, "settings": mapping, "settings_schema": mapping,
    "capabilities": {**obj({c: cap for c in capabilities}), "minProperties": 1, "maxProperties": 1}}, ["id", "capabilities"]))
solver = call
save("catalog", obj({"version": {"const": "1.0.0"}, "plugins": {"type": "array", "items": {"oneOf": [
    {"$ref": BASE + "plugin.json"}, obj({"use": string, "settings": mapping, "execution": execution}, ["use"])]}},
    "defaults": {"type": "object", "properties": {"data_transfer": call}, "additionalProperties": False},
    "runtime": mapping, "solver": solver, "extension_schemas": {"type": "object", "additionalProperties": string}}, ["version", "plugins"]))
sequence_call = obj({"plugin": string, "settings": mapping, "scope": {"enum": ["inventory", "available"]}}, ["plugin"])
req = obj({"version": {"const": "1.0.0"}, "goal": {"$ref": BASE + "goal.json"}, "sources": strings,
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
        {"type": "string", "pattern": "^path:.+"}, obj({"publish": publish, "transfer": transfer})]}}}, ["plugin"])
step["patternProperties"] = {"^param:.+": {}}
req["properties"]["steps"] = {"type": "object", "minProperties": 1, "additionalProperties": {"oneOf": [step, obj({"auto": {"const": True}}, ["auto"])]}}
save("request", req)
save("config", obj({"catalog": {"$ref": BASE + "catalog.json"}, "request": {"$ref": BASE + "request.json"}}, ["request"]))
save("goal", {"type": "object", "minProperties": 1})
