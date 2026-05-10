from __future__ import annotations

import json
import os
from pathlib import Path

import boto3


def main():
    bucket = os.getenv("TRAINING_ARTIFACT_BUCKET", "").strip()
    prefix = os.getenv("TRAINING_ARTIFACT_PREFIX", "daily-rank-training").strip().strip("/")
    target_dir_raw = os.getenv("TRAINING_MODEL_DIR", "").strip()

    if not bucket:
        raise RuntimeError("TRAINING_ARTIFACT_BUCKET is required")
    if not target_dir_raw:
        raise RuntimeError("TRAINING_MODEL_DIR is required")
    target_dir = Path(target_dir_raw).expanduser().resolve()

    region_name = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    client = boto3.client("s3", region_name=region_name)

    latest_key = "/".join(part for part in [prefix, "latest/latest_training_manifest.json"] if part)
    latest_obj = client.get_object(Bucket=bucket, Key=latest_key)
    latest_payload = json.loads(latest_obj["Body"].read().decode("utf-8"))

    manifest_key = latest_payload["manifest_key"]
    manifest_obj = client.get_object(Bucket=bucket, Key=manifest_key)
    manifest_payload = json.loads(manifest_obj["Body"].read().decode("utf-8"))

    target_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for item in manifest_payload.get("files", []):
        local_name = Path(item["local_path"]).name
        if not local_name.startswith("xgb_model_all_tiers"):
            continue

        destination = target_dir / local_name
        client.download_file(bucket, item["s3_key"], str(destination))
        downloaded.append(str(destination))

    if not downloaded:
        raise RuntimeError("No model artifacts were found in the latest training manifest.")

    print(json.dumps({
        "bucket": bucket,
        "latest_manifest_key": latest_key,
        "manifest_key": manifest_key,
        "downloaded_files": downloaded,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
