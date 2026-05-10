from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import boto3


@dataclass
class PublishedArtifact:
    local_path: str
    s3_key: str
    content_type: Optional[str] = None


class S3ArtifactPublisher:
    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "",
        region_name: Optional[str] = None,
    ):
        if not bucket:
            raise ValueError("bucket is required for S3ArtifactPublisher")

        self.bucket = bucket
        self.prefix = prefix.strip("/").replace("\\", "/")
        self.region_name = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        self.client = boto3.client("s3", region_name=self.region_name)

    @classmethod
    def from_env(cls) -> Optional["S3ArtifactPublisher"]:
        bucket = os.getenv("TRAINING_ARTIFACT_BUCKET", "").strip()
        if not bucket:
            return None
        prefix = os.getenv("TRAINING_ARTIFACT_PREFIX", "daily-rank-training").strip()
        return cls(bucket=bucket, prefix=prefix)

    def _join_key(self, *parts: str) -> str:
        sanitized_parts = [part.strip("/").replace("\\", "/") for part in parts if part]
        if self.prefix:
            sanitized_parts.insert(0, self.prefix)
        return "/".join(sanitized_parts)

    def upload_file(self, local_path: Path | str, s3_key: str) -> PublishedArtifact:
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Artifact not found: {local_path}")

        extra_args = {}
        content_type, _ = mimetypes.guess_type(local_path.name)
        if content_type:
            extra_args["ContentType"] = content_type

        final_key = self._join_key(s3_key)
        upload_kwargs = {
            "Filename": str(local_path),
            "Bucket": self.bucket,
            "Key": final_key,
        }
        if extra_args:
            upload_kwargs["ExtraArgs"] = extra_args

        self.client.upload_file(**upload_kwargs)
        return PublishedArtifact(
            local_path=str(local_path),
            s3_key=final_key,
            content_type=content_type,
        )

    def upload_files(self, files: Iterable[tuple[Path | str, str]]) -> list[PublishedArtifact]:
        published: list[PublishedArtifact] = []
        for local_path, s3_key in files:
            published.append(self.upload_file(local_path, s3_key))
        return published

    def upload_json(self, payload: dict, s3_key: str) -> PublishedArtifact:
        final_key = self._join_key(s3_key)
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.client.put_object(
            Bucket=self.bucket,
            Key=final_key,
            Body=body,
            ContentType="application/json; charset=utf-8",
        )
        return PublishedArtifact(
            local_path="__json__",
            s3_key=final_key,
            content_type="application/json; charset=utf-8",
        )

    def publish_manifest(
        self,
        *,
        pipeline_name: str,
        cutoff_datetime: datetime,
        artifact_group: str,
        files: list[PublishedArtifact],
        metadata: Optional[dict] = None,
    ) -> PublishedArtifact:
        timestamp = cutoff_datetime.strftime("%Y%m%dT%H%M%S")
        manifest_key = self._join_key(
            pipeline_name,
            artifact_group,
            timestamp,
            "manifest.json",
        )
        manifest_payload = {
            "pipeline": pipeline_name,
            "artifact_group": artifact_group,
            "cutoff_datetime": cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bucket": self.bucket,
            "files": [
                {
                    "local_path": item.local_path,
                    "s3_key": item.s3_key,
                    "content_type": item.content_type,
                }
                for item in files
            ],
            "metadata": metadata or {},
        }
        self.client.put_object(
            Bucket=self.bucket,
            Key=manifest_key,
            Body=json.dumps(manifest_payload, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
        )
        return PublishedArtifact(
            local_path="__manifest__",
            s3_key=manifest_key,
            content_type="application/json; charset=utf-8",
        )
