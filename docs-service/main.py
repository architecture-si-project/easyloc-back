import copy
import json
import os

import requests
from flask import Flask, Response, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint


DEFAULT_SPEC_URLS = [
    "http://user-service:5000/openapi.json",
    "http://housing-service:5000/openapi.json",
    "http://reservation-service:5000/openapi.json",
]

SERVICE_BASE_URLS = {
    "auth": "http://user-service:5000",
    "users": "http://user-service:5000",
    "housing": "http://housing-service:5000",
    "reservations": "http://reservation-service:5000",
}


def _read_spec_urls():
    raw = os.getenv("SOURCE_OPENAPI_URLS")
    if not raw:
        return DEFAULT_SPEC_URLS

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    return DEFAULT_SPEC_URLS


def _fetch_openapi(url):
    response = requests.get(url, timeout=4)
    response.raise_for_status()
    return response.json()


def _merge_component_dict(target, source, component_name):
    if not isinstance(source, dict):
        return

    target.setdefault("components", {})
    target["components"].setdefault(component_name, {})

    for key, value in source.items():
        if key not in target["components"][component_name]:
            target["components"][component_name][key] = copy.deepcopy(value)


def _merge_openapi_specs(specs):
    merged = {
        "openapi": "3.0.3",
        "info": {"title": "EasyLoc Unified API", "version": "1.0.0"},
        "servers": [{"url": "/"}],
        "tags": [],
        "paths": {},
        "components": {},
    }

    seen_tags = set()

    for spec in specs:
        for tag in spec.get("tags", []):
            tag_name = tag.get("name")
            if tag_name and tag_name not in seen_tags:
                merged["tags"].append(tag)
                seen_tags.add(tag_name)

        for path, methods in spec.get("paths", {}).items():
            merged["paths"][path] = methods

        source_components = spec.get("components", {})
        for component_name in [
            "schemas",
            "securitySchemes",
            "parameters",
            "responses",
            "requestBodies",
        ]:
            _merge_component_dict(merged, source_components.get(component_name), component_name)

    return merged


def _target_url(path: str):
    first_segment = path.split("/", 1)[0]
    base_url = SERVICE_BASE_URLS.get(first_segment)
    if not base_url:
        return None
    return f"{base_url}/{path}"


def _forward_request(path: str):
    target = _target_url(path)
    if not target:
        return jsonify({"error": "Route not proxied by docs-service"}), 404

    headers = {}
    for name in ["Authorization", "Content-Type", "Accept"]:
        value = request.headers.get(name)
        if value:
            headers[name] = value

    upstream = requests.request(
        method=request.method,
        url=target,
        params=request.args,
        data=request.get_data(),
        headers=headers,
        timeout=15,
    )

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in {"content-encoding", "transfer-encoding", "connection"}
    }

    return Response(upstream.content, status=upstream.status_code, headers=response_headers)


app = Flask(__name__)

swagger_ui_blueprint = get_swaggerui_blueprint(
    "/docs",
    "/openapi.json",
    config={"app_name": "EasyLoc Unified API Docs"},
)
app.register_blueprint(swagger_ui_blueprint, url_prefix="/docs")


@app.get("/openapi.json")
def openapi_json():
    specs = []
    errors = []

    for url in _read_spec_urls():
        try:
            specs.append(_fetch_openapi(url))
        except Exception as exc:
            errors.append({"url": url, "error": str(exc)})

    if not specs:
        return jsonify({"error": "Unable to load OpenAPI specs", "details": errors}), 503

    merged = _merge_openapi_specs(specs)
    if errors:
        merged["x-docs-warnings"] = errors

    return jsonify(merged)


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def proxy(path):
    return _forward_request(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
