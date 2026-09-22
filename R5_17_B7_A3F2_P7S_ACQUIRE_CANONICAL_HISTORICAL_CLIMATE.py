#!/usr/bin/env python3
"""Sequentially acquire the governed Krapp and Beyer climate source files.

Default execution performs network preflight and acquisition. Use --validate-only
for an offline manifest check. Provider payloads and the mutable run ledger stay
outside the repository. This tool does not extract climate values or run P7S.
"""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "R5.17-B7-A3F2-P7S-CANONICAL-CLIMATE-CACHE"
REPO = Path(__file__).resolve().parent
MANIFEST_PATH = REPO / "R5_17_B7_A3F2_P7S_CANONICAL_CLIMATE_ACQUISITION_MANIFEST.json"
EXTERNAL_ROOT = Path(r"F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld_ARCANA_EXTERNAL_SOURCES\p7q_parent_state")
CACHE_ROOT = EXTERNAL_ROOT / "P7S_HISTORICAL_CLIMATE"
LEDGER_PATH = CACHE_ROOT / "manifest" / "P7S_CANONICAL_CLIMATE_ACQUISITION_RUN_LEDGER.json"
MAX_METADATA_BYTES = 16 * 1024 * 1024
BLOCK_BYTES = 1024 * 1024
MAX_RETRIES = 5
MAX_RETRY_AFTER_SECONDS = 300
USER_AGENT = "ARCANA-P7S-canonical-cache/1.0 (Python urllib; verified TLS)"
EXPECTED_TOTAL_FILES = 14
EXPECTED_TOTAL_BYTES = 3_600_803_435
EXPECTED_FILES = {
    "temp_800ka_ann.nc": ("KRAPP_2021_800KA", 146088257, "https://osf.io/download/7m94u/"),
    "prec_800ka_jan.nc": ("KRAPP_2021_800KA", 170729674, "https://osf.io/download/6khc8/"),
    "prec_800ka_feb.nc": ("KRAPP_2021_800KA", 170027313, "https://osf.io/download/5s6tp/"),
    "prec_800ka_mar.nc": ("KRAPP_2021_800KA", 171090765, "https://osf.io/download/8yhz9/"),
    "prec_800ka_apr.nc": ("KRAPP_2021_800KA", 170747248, "https://osf.io/download/6mq2r/"),
    "prec_800ka_may.nc": ("KRAPP_2021_800KA", 174419384, "https://osf.io/download/dn8pe/"),
    "prec_800ka_jun.nc": ("KRAPP_2021_800KA", 181229336, "https://osf.io/download/pzywf/"),
    "prec_800ka_jul.nc": ("KRAPP_2021_800KA", 185846054, "https://osf.io/download/wxzhe/"),
    "prec_800ka_aug.nc": ("KRAPP_2021_800KA", 187486854, "https://osf.io/download/c84ve/"),
    "prec_800ka_sep.nc": ("KRAPP_2021_800KA", 187731972, "https://osf.io/download/p84xn/"),
    "prec_800ka_oct.nc": ("KRAPP_2021_800KA", 182019485, "https://osf.io/download/utfsa/"),
    "prec_800ka_nov.nc": ("KRAPP_2021_800KA", 169876345, "https://osf.io/download/wavsd/"),
    "prec_800ka_dec.nc": ("KRAPP_2021_800KA", 170274112, "https://osf.io/download/h5eq7/"),
    "LateQuaternary_Environment.nc": ("BEYER_KRAPP_MANICA_120KA", 1333236636,
                                      "https://ndownloader.figshare.com/files/22659026"),
}


class AcquisitionError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    data = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def load_manifest() -> dict[str, Any]:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcquisitionError(f"Cannot load tracked acquisition manifest: {exc}") from exc


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    files = manifest.get("files")
    if manifest.get("stage") != STAGE or not isinstance(files, list):
        raise AcquisitionError("Manifest stage/schema mismatch")
    if len(files) != EXPECTED_TOTAL_FILES:
        raise AcquisitionError(f"Expected exactly {EXPECTED_TOTAL_FILES} files, found {len(files)}")
    total = sum(int(item["expected_bytes"]) for item in files)
    if total != EXPECTED_TOTAL_BYTES or manifest.get("total_expected_bytes") != EXPECTED_TOTAL_BYTES:
        raise AcquisitionError(f"Expected-byte ledger mismatch: computed={total}, required={EXPECTED_TOTAL_BYTES}")
    names = [item["filename"] for item in files]
    if len(set(names)) != len(names):
        raise AcquisitionError("Duplicate acquisition filename in manifest")
    if set(names) != set(EXPECTED_FILES):
        raise AcquisitionError("Manifest filenames differ from the pinned 14-file target set")
    for item in files:
        expected_provider, expected_size, expected_url = EXPECTED_FILES[item["filename"]]
        if (item.get("provider"), item.get("expected_bytes"), item.get("canonical_download_url")) != (
                expected_provider, expected_size, expected_url):
            raise AcquisitionError(f"Pinned provider/size/URL mismatch for {item['filename']}")
    krapp = [item for item in files if item["provider"] == "KRAPP_2021_800KA"]
    beyer = [item for item in files if item["provider"] == "BEYER_KRAPP_MANICA_120KA"]
    if len(krapp) != 13 or len(beyer) != 1:
        raise AcquisitionError(f"Wrong provider file counts: Krapp={len(krapp)}, Beyer={len(beyer)}")
    forbidden = {"temp_800ka_jan.nc", "temp_800ka_feb.nc", "temp_800ka_mar.nc", "temp_800ka_apr.nc",
                 "temp_800ka_may.nc", "temp_800ka_jun.nc", "temp_800ka_jul.nc", "temp_800ka_aug.nc",
                 "temp_800ka_sep.nc", "temp_800ka_oct.nc", "temp_800ka_nov.nc", "temp_800ka_dec.nc"}
    if forbidden.intersection(names):
        raise AcquisitionError("Manifest includes explicitly excluded monthly-temperature files")
    return files


def request_with_retry(request: urllib.request.Request, label: str):
    """Open one sequential HTTPS request with bounded retry/backoff."""
    for attempt in range(MAX_RETRIES + 1):
        if RUN_LEDGER is not None:
            RUN_LEDGER["request_attempt_count"] = RUN_LEDGER.get("request_attempt_count", 0) + 1
            record_event(label, "REQUEST_ATTEMPT", attempt=attempt + 1)
        try:
            response = urllib.request.urlopen(request, timeout=90, context=ssl.create_default_context())
            if RUN_LEDGER is not None:
                counts = RUN_LEDGER.setdefault("http_status_counts", {})
                counts[str(response.status)] = counts.get(str(response.status), 0) + 1
                record_event(label, "HTTP_RESPONSE", status=response.status)
            return response
        except urllib.error.HTTPError as exc:
            status = exc.code
            if RUN_LEDGER is not None:
                counts = RUN_LEDGER.setdefault("http_status_counts", {})
                counts[str(status)] = counts.get(str(status), 0) + 1
                record_event(label, "HTTP_RESPONSE", status=status)
            retryable = status == 429 or 500 <= status <= 599
            if not retryable or attempt >= MAX_RETRIES:
                raise AcquisitionError(f"{label}: HTTP {status}; stopped after {attempt + 1} attempt(s)") from exc
            delay = retry_delay(exc.headers.get("Retry-After"), attempt)
            if RUN_LEDGER is not None:
                RUN_LEDGER["retry_count"] = RUN_LEDGER.get("retry_count", 0) + 1
            record_event(label, f"HTTP_{status}_RETRY", retry_after_seconds=delay, attempt=attempt + 1)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt >= MAX_RETRIES:
                raise AcquisitionError(f"{label}: transport failed after {attempt + 1} attempt(s): {exc}") from exc
            delay = min(2**attempt, MAX_RETRY_AFTER_SECONDS)
            if RUN_LEDGER is not None:
                RUN_LEDGER["retry_count"] = RUN_LEDGER.get("retry_count", 0) + 1
            record_event(label, "TRANSPORT_RETRY", retry_after_seconds=delay, attempt=attempt + 1)
            time.sleep(delay)
    raise AcquisitionError(f"{label}: retry loop exhausted")


RUN_LEDGER: dict[str, Any] | None = None


def record_event(label: str, event: str, **fields: Any) -> None:
    if RUN_LEDGER is None:
        return
    RUN_LEDGER.setdefault("events", []).append({"timestamp": utc_now(), "target": label, "event": event, **fields})
    atomic_json(LEDGER_PATH, RUN_LEDGER)


def retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return min(max(float(value), 0.0), MAX_RETRY_AFTER_SECONDS)
        except ValueError:
            try:
                when = email.utils.parsedate_to_datetime(value)
                return min(max((when - datetime.now(when.tzinfo or timezone.utc)).total_seconds(), 0.0),
                           MAX_RETRY_AFTER_SECONDS)
            except (TypeError, ValueError, OverflowError):
                pass
    return min(2**attempt, MAX_RETRY_AFTER_SECONDS)


def read_json(url: str, label: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with request_with_retry(request, label) as response:
        if response.status != 200:
            raise AcquisitionError(f"{label}: metadata HTTP status {response.status}, expected 200")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_METADATA_BYTES:
            raise AcquisitionError(f"{label}: metadata response exceeds safety limit")
        body = response.read(MAX_METADATA_BYTES + 1)
        if len(body) > MAX_METADATA_BYTES:
            raise AcquisitionError(f"{label}: metadata response exceeds safety limit")
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcquisitionError(f"{label}: invalid JSON metadata") from exc
    if not isinstance(value, dict):
        raise AcquisitionError(f"{label}: unexpected metadata JSON shape")
    return value


def find_license(node: Any, path: str = "") -> tuple[str | None, str | None, str | None]:
    """Extract only explicit license fields; never infer from a citation/default."""
    if isinstance(node, dict):
        for key in ("node_license", "license"):
            candidate = node.get(key)
            if isinstance(candidate, dict):
                name = next((candidate.get(k) for k in ("name", "title", "value", "identifier", "id")
                             if isinstance(candidate.get(k), str) and candidate.get(k).strip()), None)
                uri = next((candidate.get(k) for k in ("url", "uri", "license_url")
                            if isinstance(candidate.get(k), str) and candidate.get(k).strip()), None)
                if name:
                    return name.strip(), uri, f"{path}/{key}"
            elif isinstance(candidate, str) and candidate.strip():
                uri = node.get("license_url") or node.get("license_uri")
                return candidate.strip(), uri if isinstance(uri, str) else None, f"{path}/{key}"
        for key, value in node.items():
            result = find_license(value, f"{path}/{key}")
            if result[0]:
                return result
    elif isinstance(node, list):
        for index, value in enumerate(node):
            result = find_license(value, f"{path}[{index}]")
            if result[0]:
                return result
    return None, None, None


def iter_osf_file_records(url: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    next_url: str | None = url
    pages = 0
    while next_url:
        pages += 1
        if pages > 100:
            raise AcquisitionError("OSF file metadata pagination exceeded 100 pages")
        page = read_json(next_url, "OSF_FILE_METADATA")
        data = page.get("data")
        if not isinstance(data, list):
            raise AcquisitionError("OSF file metadata has no data list")
        records.extend(item for item in data if isinstance(item, dict))
        links = page.get("links", {})
        next_url = links.get("next") if isinstance(links, dict) else None
        if next_url and not str(next_url).startswith("https://api.osf.io/"):
            raise AcquisitionError("OSF pagination returned a non-canonical API URL")
    return records


def url_identity(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(url)
    return (parsed.netloc.lower(), parsed.path.rstrip("/").lower())


def verify_osf(metadata: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, Any]:
    source = metadata["providers"]["KRAPP_2021_800KA"]
    node = read_json(source["canonical_metadata_source"], "OSF_PROJECT_METADATA")
    if not isinstance(node.get("data"), dict):
        raise AcquisitionError("OSF project metadata lacks data object")
    license_name, license_uri, license_path = find_license(node["data"], "data")
    osf_files = iter_osf_file_records(source["files_metadata_source"])
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in osf_files:
        attrs = item.get("attributes", {})
        if isinstance(attrs, dict) and isinstance(attrs.get("name"), str):
            by_name.setdefault(attrs["name"], []).append(item)
    for item in files:
        if item["provider"] != "KRAPP_2021_800KA":
            continue
        matches = by_name.get(item["filename"], [])
        if len(matches) != 1:
            raise AcquisitionError(f"OSF metadata must identify exactly one {item['filename']}; got {len(matches)}")
        rec = matches[0]
        attrs = rec.get("attributes", {})
        size = attrs.get("size") if isinstance(attrs, dict) else None
        if size != item["expected_bytes"]:
            raise AcquisitionError(f"OSF size discrepancy for {item['filename']}: metadata={size}, expected={item['expected_bytes']}")
        links = rec.get("links", {})
        download = links.get("download") if isinstance(links, dict) else None
        if not isinstance(download, str) or url_identity(download) != url_identity(item["canonical_download_url"]):
            raise AcquisitionError(f"OSF canonical download identity changed/unverifiable for {item['filename']}")
    if not license_name:
        return {"name": None, "uri": None, "status": "LICENSE_METADATA_UNRESOLVED", "metadata_source": source["canonical_metadata_source"], "field_path": None, "retrieved_utc": utc_now()}
    return {"name": license_name, "uri": license_uri, "status": "CAPTURED", "metadata_source": source["canonical_metadata_source"], "field_path": license_path, "retrieved_utc": utc_now()}


def verify_figshare(metadata: dict[str, Any], files: list[dict[str, Any]]) -> dict[str, Any]:
    source = metadata["providers"]["BEYER_KRAPP_MANICA_120KA"]
    article = read_json(source["canonical_metadata_source"], "FIGSHARE_ARTICLE_V3_METADATA")
    version = article.get("version", article.get("version_number"))
    if version != 3:
        raise AcquisitionError(f"Figshare exact v3 metadata mismatch: returned version={version!r}; stopped before download")
    if str(article.get("doi", "")).lower() != "10.6084/m9.figshare.12293345.v3":
        raise AcquisitionError("Figshare DOI does not identify the specifically authorized v3")
    targets = [item for item in files if item["provider"] == "BEYER_KRAPP_MANICA_120KA"]
    if len(targets) != 1:
        raise AcquisitionError("Manifest must contain exactly one Beyer file")
    target = targets[0]
    matches = [f for f in article.get("files", []) if isinstance(f, dict) and f.get("name") == target["filename"]]
    if len(matches) != 1:
        raise AcquisitionError(f"Figshare v3 must identify exactly one {target['filename']}; got {len(matches)}")
    file_meta = matches[0]
    if file_meta.get("id") != 22659026 or file_meta.get("size") != target["expected_bytes"]:
        raise AcquisitionError(f"Figshare file id/size mismatch for v3: {file_meta.get('id')}/{file_meta.get('size')}")
    metadata_download = file_meta.get("download_url")
    if not isinstance(metadata_download, str) or url_identity(metadata_download) != url_identity(target["canonical_download_url"]):
        raise AcquisitionError("Figshare v3 canonical file URL changed/unverifiable; stopped before download")
    license_name, license_uri, license_path = find_license(article, "article")
    if not license_name:
        return {"name": None, "uri": None, "status": "LICENSE_METADATA_UNRESOLVED", "metadata_source": source["canonical_metadata_source"], "field_path": None, "retrieved_utc": utc_now()}
    return {"name": license_name, "uri": license_uri, "status": "CAPTURED", "metadata_source": source["canonical_metadata_source"], "field_path": license_path, "retrieved_utc": utc_now()}


def update_license(manifest: dict[str, Any], provider: str, license_info: dict[str, Any]) -> None:
    stored = manifest["providers"][provider].get("license")
    if isinstance(stored, dict) and stored.get("status") == "CAPTURED":
        if stored.get("name") != license_info.get("name") or stored.get("uri") != license_info.get("uri"):
            raise AcquisitionError(f"{provider} license metadata changed; manual review required")
    manifest["providers"][provider]["license"] = license_info
    for item in manifest["files"]:
        if item["provider"] == provider:
            item["license"] = license_info.copy()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(BLOCK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()


def validate_existing(item: dict[str, Any], final_path: Path) -> str:
    actual_size = final_path.stat().st_size
    if actual_size != item["expected_bytes"]:
        raise AcquisitionError(f"STOP_SIZE_MISMATCH: {final_path} is {actual_size}, expected {item['expected_bytes']}; not overwritten")
    actual_hash = sha256_file(final_path)
    recorded = item.get("sha256")
    if recorded and actual_hash.lower() != recorded.lower():
        raise AcquisitionError(f"STOP_HASH_MISMATCH: {final_path}; not overwritten")
    return actual_hash


def parse_content_range(value: str | None) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"bytes\s+(\d+)-(\d+)/(\d+)", value or "", re.IGNORECASE)
    return tuple(map(int, match.groups())) if match else None


def download_one(item: dict[str, Any], manifest: dict[str, Any]) -> None:
    provider_root = CACHE_ROOT / item["provider_dir"]
    raw_dir = provider_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (provider_root / "manifest").mkdir(parents=True, exist_ok=True)
    final_path = raw_dir / item["filename"]
    partial_path = raw_dir / (item["filename"] + ".partial")

    if final_path.exists():
        digest = validate_existing(item, final_path)
        if not item.get("sha256"):
            item["status"] = "EXISTING_HASHED_ORIGIN_UNATTESTED"
            item["actual_bytes"] = final_path.stat().st_size
            item["sha256"] = digest
            item["retrieval_timestamp"] = None
            item["transport"] = "LOCAL_EXISTING_FILE; ORIGINAL_RETRIEVAL_UNATTESTED"
            atomic_json(MANIFEST_PATH, manifest)
            record_event(item["filename"], "EXISTING_HASHED_ORIGIN_UNATTESTED", sha256=digest)
            raise AcquisitionError(f"Existing file has no previously recorded acquisition hash; captured local hash but will not claim canonical provenance or redownload: {final_path}")
        item["status"] = "REUSE_VALID_CACHE"
        item["actual_bytes"] = final_path.stat().st_size
        item["sha256"] = digest
        manifest["total_actual_bytes"] = sum(x.get("actual_bytes") or 0 for x in manifest["files"])
        atomic_json(MANIFEST_PATH, manifest)
        record_event(item["filename"], "REUSE_VALID_CACHE", bytes=item["actual_bytes"], sha256=digest)
        return

    if partial_path.exists() and partial_path.stat().st_size > item["expected_bytes"]:
        raise AcquisitionError(f"STOP_PARTIAL_OVERSIZE: {partial_path}; preserved without modification")

    ledger_files = RUN_LEDGER.setdefault("files", {})
    state = ledger_files.setdefault(item["filename"], {})
    offset = partial_path.stat().st_size if partial_path.exists() else 0
    if offset == item["expected_bytes"] and offset > 0:
        digest = sha256_file(partial_path)
        if item.get("sha256") and item["sha256"].lower() != digest.lower():
            raise AcquisitionError(f"Complete .partial hash mismatch for {item['filename']}; preserved")
        item["actual_bytes"] = offset
        item["sha256"] = digest
        item["retrieval_timestamp"] = state.get("download_started_utc")
        item["transport"] = "RESUMED_PARTIAL; range ledger and complete-file SHA256"
        item["status"] = "DOWNLOAD_VERIFIED_PENDING_ATOMIC_RENAME"
        atomic_json(MANIFEST_PATH, manifest)
        if final_path.exists():
            raise AcquisitionError(f"Final target appeared while validating partial; refusing overwrite: {final_path}")
        os.rename(partial_path, final_path)
        item["status"] = "ACQUIRED_VALIDATED"
        state["status"] = "ACQUIRED_VALIDATED"
        state["partial_bytes"] = 0
        state["actual_bytes"] = offset
        state["sha256"] = digest
        state["completed_utc"] = utc_now()
        manifest["total_actual_bytes"] = sum(x.get("actual_bytes") or 0 for x in manifest["files"])
        atomic_json(MANIFEST_PATH, manifest)
        atomic_json(LEDGER_PATH, RUN_LEDGER)
        return
    if offset:
        validator = state.get("etag") or state.get("last_modified")
        if not validator:
            raise AcquisitionError(f"RESUME_VALIDATOR_UNAVAILABLE: preserving {partial_path}; no prior ETag/Last-Modified to bind the range")
        headers = {"Range": f"bytes={offset}-", "If-Range": validator, "User-Agent": USER_AGENT}
        mode = "ab"
    else:
        headers = {"User-Agent": USER_AGENT}
        mode = "wb"
        state["download_started_utc"] = utc_now()
    request = urllib.request.Request(item["canonical_download_url"], headers=headers, method="GET")
    with request_with_retry(request, item["filename"]) as response:
        expected_status = 206 if offset else 200
        if response.status != expected_status:
            raise AcquisitionError(f"{item['filename']}: HTTP {response.status}, expected {expected_status}; partial preserved")
        content_length = response.headers.get("Content-Length")
        expected_response_bytes = item["expected_bytes"] - offset
        if content_length is None or int(content_length) != expected_response_bytes:
            raise AcquisitionError(f"{item['filename']}: Content-Length mismatch/missing; partial preserved")
        if offset:
            content_range = parse_content_range(response.headers.get("Content-Range"))
            if content_range != (offset, item["expected_bytes"] - 1, item["expected_bytes"]):
                raise AcquisitionError(f"{item['filename']}: Content-Range mismatch; partial preserved")
        else:
            if response.headers.get("Content-Range"):
                raise AcquisitionError(f"{item['filename']}: unexpected partial response to full-object request")
        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
        if offset and state.get("etag") and etag and state["etag"] != etag:
            raise AcquisitionError(f"{item['filename']}: ETag changed during resume; partial preserved")
        if offset and state.get("last_modified") and last_modified and state["last_modified"] != last_modified:
            raise AcquisitionError(f"{item['filename']}: Last-Modified changed during resume; partial preserved")
        if etag:
            state["etag"] = etag
        if last_modified:
            state["last_modified"] = last_modified
        state["expected_bytes"] = item["expected_bytes"]
        state["last_http_status"] = response.status
        state["last_response_utc"] = utc_now()
        atomic_json(LEDGER_PATH, RUN_LEDGER)
        digest = hashlib.sha256()
        if offset:
            with partial_path.open("rb") as existing:
                while chunk := existing.read(BLOCK_BYTES):
                    digest.update(chunk)
        received = offset
        try:
            with partial_path.open(mode) as output:
                while chunk := response.read(BLOCK_BYTES):
                    output.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                    if received > item["expected_bytes"]:
                        raise AcquisitionError(f"{item['filename']}: received more than expected; partial preserved")
                    if received % (16 * BLOCK_BYTES) < len(chunk):
                        output.flush()
                        os.fsync(output.fileno())
                        state["partial_bytes"] = received
                        state["checkpoint_utc"] = utc_now()
                        atomic_json(LEDGER_PATH, RUN_LEDGER)
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            state["partial_bytes"] = partial_path.stat().st_size if partial_path.exists() else 0
            state["status"] = "PARTIAL_PRESERVED"
            state["checkpoint_utc"] = utc_now()
            atomic_json(LEDGER_PATH, RUN_LEDGER)
            raise
    actual_size = partial_path.stat().st_size
    if received != item["expected_bytes"] or actual_size != item["expected_bytes"]:
        state["partial_bytes"] = actual_size
        state["status"] = "PARTIAL_PRESERVED"
        atomic_json(LEDGER_PATH, RUN_LEDGER)
        raise AcquisitionError(f"{item['filename']}: final size mismatch; partial preserved ({actual_size}/{item['expected_bytes']})")
    actual_hash = digest.hexdigest()
    if item.get("sha256") and item["sha256"].lower() != actual_hash.lower():
        raise AcquisitionError(f"{item['filename']}: hash mismatch against manifest; partial preserved; no overwrite")

    item["actual_bytes"] = actual_size
    item["sha256"] = actual_hash
    item["retrieval_timestamp"] = utc_now()
    item["transport"] = "urllib.request + ssl.create_default_context; sequential HTTPS; verified Content-Length; SHA256 streamed"
    item["status"] = "DOWNLOAD_VERIFIED_PENDING_ATOMIC_RENAME"
    manifest["total_actual_bytes"] = sum(x.get("actual_bytes") or 0 for x in manifest["files"])
    atomic_json(MANIFEST_PATH, manifest)
    if final_path.exists():
        raise AcquisitionError(f"Final target appeared during acquisition; refusing overwrite: {final_path}")
    os.rename(partial_path, final_path)
    item["status"] = "ACQUIRED_VALIDATED"
    state["status"] = "ACQUIRED_VALIDATED"
    state["partial_bytes"] = 0
    state["actual_bytes"] = actual_size
    state["sha256"] = actual_hash
    state["completed_utc"] = utc_now()
    atomic_json(MANIFEST_PATH, manifest)
    atomic_json(LEDGER_PATH, RUN_LEDGER)
    record_event(item["filename"], "ACQUIRED_VALIDATED", bytes=actual_size, sha256=actual_hash)


def summarize(manifest: dict[str, Any]) -> tuple[int, int, bool]:
    files = manifest["files"]
    actual_total = 0
    all_valid = len(files) == EXPECTED_TOTAL_FILES
    partial_count = 0
    for item in files:
        raw = CACHE_ROOT / item["provider_dir"] / "raw"
        final = raw / item["filename"]
        partial = raw / (item["filename"] + ".partial")
        if partial.exists():
            partial_count += 1
        if not final.is_file():
            all_valid = False
            continue
        actual = final.stat().st_size
        actual_total += actual
        if actual != item["expected_bytes"] or not item.get("sha256") or sha256_file(final) != item["sha256"]:
            all_valid = False
    unexpected_partials = list(CACHE_ROOT.rglob("*.partial")) if CACHE_ROOT.exists() else []
    partial_count = max(partial_count, len(unexpected_partials))
    all_valid = all_valid and actual_total == EXPECTED_TOTAL_BYTES and partial_count == 0
    return actual_total, partial_count, all_valid


def main() -> int:
    global RUN_LEDGER
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-only", action="store_true", help="offline manifest/count check; performs no network or filesystem mutation")
    args = parser.parse_args()
    try:
        manifest = load_manifest()
        files = validate_manifest(manifest)
        if args.validate_only:
            print(f"MANIFEST_VALID files={len(files)} expected_bytes={EXPECTED_TOTAL_BYTES}; network=0; writes=0")
            return 0
        if REPO in EXTERNAL_ROOT.resolve().parents or EXTERNAL_ROOT.resolve() == REPO:
            raise AcquisitionError("External cache root resolves inside the Git repository")
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        RUN_LEDGER = {"stage": STAGE, "started_utc": utc_now(), "status": "PREFLIGHT", "events": [], "files": {}}
        atomic_json(LEDGER_PATH, RUN_LEDGER)

        krapp_license = verify_osf(manifest, files)
        beyer_license = verify_figshare(manifest, files)
        update_license(manifest, "KRAPP_2021_800KA", krapp_license)
        update_license(manifest, "BEYER_KRAPP_MANICA_120KA", beyer_license)
        for provider in ("KRAPP_2021_800KA", "BEYER_KRAPP_MANICA_120KA"):
            if manifest["providers"][provider]["license"].get("status") != "CAPTURED":
                manifest["acquisition_status"] = "BLOCKED_LICENSE_METADATA_UNRESOLVED"
                atomic_json(MANIFEST_PATH, manifest)
                raise AcquisitionError(f"{provider}: LICENSE_METADATA_UNRESOLVED; stopped before payload download")
        atomic_json(MANIFEST_PATH, manifest)
        RUN_LEDGER["status"] = "ACQUIRING_SEQUENTIAL"
        RUN_LEDGER["provider_metadata"] = {
            "KRAPP_2021_800KA": krapp_license,
            "BEYER_KRAPP_MANICA_120KA": beyer_license,
            "captured_utc": utc_now(),
        }
        atomic_json(LEDGER_PATH, RUN_LEDGER)
        (CACHE_ROOT / "KRAPP_800K" / "raw").mkdir(parents=True, exist_ok=True)
        (CACHE_ROOT / "KRAPP_800K" / "manifest").mkdir(parents=True, exist_ok=True)
        (CACHE_ROOT / "BEYER_120K" / "raw").mkdir(parents=True, exist_ok=True)
        (CACHE_ROOT / "BEYER_120K" / "manifest").mkdir(parents=True, exist_ok=True)
        (CACHE_ROOT / "CHELSA_TRACE21K" / "cache").mkdir(parents=True, exist_ok=True)
        (CACHE_ROOT / "CHELSA_TRACE21K" / "manifest").mkdir(parents=True, exist_ok=True)

        # Stable manifest order is intentionally sequential; no worker pool is used.
        for item in files:
            if item.get("status") == "EXISTING_HASHED_ORIGIN_UNATTESTED":
                raise AcquisitionError(f"{item['filename']}: existing source-origin status requires human review")
            download_one(item, manifest)

        actual_total, partial_count, ready = summarize(manifest)
        if ready:
            manifest["acquisition_status"] = "LOCAL_CANONICAL_PROVIDER_CACHE_READY"
            manifest["total_actual_bytes"] = actual_total
            manifest["all_hashes_verified"] = True
            manifest["r6_canonical_external_input_candidate"] = True
            RUN_LEDGER["status"] = "LOCAL_CANONICAL_PROVIDER_CACHE_READY"
        else:
            manifest["acquisition_status"] = "ACQUISITION_INCOMPLETE"
            manifest["total_actual_bytes"] = actual_total
            manifest["all_hashes_verified"] = False
            manifest["r6_canonical_external_input_candidate"] = False
            RUN_LEDGER["status"] = "ACQUISITION_INCOMPLETE"
        RUN_LEDGER["completed_utc"] = utc_now()
        RUN_LEDGER["summary"] = {"files": len(files), "actual_bytes": actual_total, "partial_files": partial_count, "ready": ready}
        atomic_json(MANIFEST_PATH, manifest)
        atomic_json(LEDGER_PATH, RUN_LEDGER)
        print(f"files={len(files)}/14 actual_bytes={actual_total} expected_bytes={EXPECTED_TOTAL_BYTES} partial_files={partial_count}")
        print(manifest["acquisition_status"])
        return 0 if ready else 2
    except AcquisitionError as exc:
        try:
            if "manifest" in locals() and isinstance(manifest, dict):
                if manifest.get("acquisition_status") != "BLOCKED_LICENSE_METADATA_UNRESOLVED":
                    manifest["acquisition_status"] = "ACQUISITION_INCOMPLETE"
                manifest["total_actual_bytes"] = sum(item.get("actual_bytes") or 0 for item in manifest.get("files", []))
                manifest["all_hashes_verified"] = False
                manifest["r6_canonical_external_input_candidate"] = False
                atomic_json(MANIFEST_PATH, manifest)
        except Exception:
            pass
        if RUN_LEDGER is not None:
            RUN_LEDGER["status"] = "ACQUISITION_INCOMPLETE"
            RUN_LEDGER["last_error"] = str(exc)
            RUN_LEDGER["updated_utc"] = utc_now()
            atomic_json(LEDGER_PATH, RUN_LEDGER)
        print(f"ACQUISITION_INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if RUN_LEDGER is not None:
            RUN_LEDGER["status"] = "ACQUISITION_INCOMPLETE"
            RUN_LEDGER["last_error"] = f"{type(exc).__name__}: {exc}"
            RUN_LEDGER["updated_utc"] = utc_now()
            atomic_json(LEDGER_PATH, RUN_LEDGER)
        print(f"ACQUISITION_INCOMPLETE: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
