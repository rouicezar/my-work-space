#!/usr/bin/env python3
"""Verify and zero-copy link an existing pinned Hugging Face model cache."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from forma_ai.models import ModelError, link_external_model, load_model


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-root", type=Path, required=True)
    parser.add_argument(
        "--cache-root", type=Path, default=Path.home() / ".cache/huggingface/hub"
    )
    parser.add_argument("--model-id", default="qwen3-0.6b-4bit-alpha")
    parser.add_argument("--catalog", type=Path, default=REPOSITORY_ROOT / "config/models.json")
    args = parser.parse_args()
    if not args.product_root.is_absolute() or not args.cache_root.is_absolute():
        print(json.dumps({"status": "failed", "code": "ROOT_NOT_ABSOLUTE"}))
        return 2
    try:
        model = load_model(args.catalog, args.model_id)
        reference = link_external_model(
            product_root=args.product_root, cache_root=args.cache_root, model=model
        )
    except Exception as exc:
        code = exc.code if isinstance(exc, ModelError) else "MODEL_LINK_FAILED"
        print(json.dumps({"status": "failed", "code": code, "message": str(exc)}))
        return 2
    print(json.dumps({"status": "linked", "reference": asdict(reference)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
