# Multilingual E5 Small MLX candidate evidence

Status: pinned candidate only. No model weights were downloaded during this investigation, and this document is not proof of a successful local inference probe.

## Selected artifact

- Repository: `mlx-community/multilingual-e5-small-mlx`
- Revision: `5030c7625865046d350eeea28f427d80353d0ac0`
- Upstream model: `intfloat/multilingual-e5-small`
- License: MIT
- Architecture: `BertModel`
- Vector dimension: 384
- Required input contract: queries use `query: `; stored content uses `passage: `.
- Exact required-file sizes and SHA-256 values are pinned in `config/models.json`.

The pinned five-file snapshot totals 252,418,075 bytes. Activation is allowed only after every required file matches the catalog, the user approves the exact revision, and the managed runtime is stopped. The product creates an external reference instead of copying or taking ownership of the Hugging Face cache.

## Compatibility evidence

The oMLX public README documents `/v1/embeddings` support for BERT-family models. The fixed oMLX v0.6.3 source recognizes `BertModel` and routes embedding models through `mlx-embeddings`. This is source-level compatibility evidence only; the release gate still requires a real local request and vector-dimension check.

Sources:

- https://github.com/jundot/omlx/blob/main/README.md
- https://huggingface.co/mlx-community/multilingual-e5-small-mlx
- https://huggingface.co/mlx-community/multilingual-e5-small-mlx/blob/main/config.json
- https://huggingface.co/intfloat/multilingual-e5-small
