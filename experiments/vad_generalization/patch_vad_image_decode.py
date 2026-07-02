#!/usr/bin/env python3
"""Fix the VAD fork's renderer-image decode (the bug that killed the first VAD smoke).

The NeuroNCAP orchestrator sends camera images as base64-encoded torch-saved TENSORS
(renderer_api.py: `torch.save(tensor, buff); base64.b64encode(...)`; model_api.py declares
`images: dict[str, str]  # utf-8 encoded base64 tensor (h, w, 3)`). The UniAD fork decodes with
`torch.load`; the VAD fork still calls `PIL.Image.open` on the tensor bytes and dies with
`UnidentifiedImageError` on the first /infer of every episode.

This patch replaces the body of `_pngs_to_numpy` with the torch.load decode, exactly mirroring
UniAD's `_bytestr_to_numpy`. It does NOT git-checkout (so it composes with the union patch, which
does); apply order: server_patch_union_vad.py first, then this. Idempotent.
"""
SRV = '/opt/sentinel-stack/VAD/inference/server.py'
src = open(SRV).read()

MARK = 'VAD_IMGFIX: torch-tensor decode'
if MARK in src:
    print('already patched')
    raise SystemExit(0)

OLD = '''def _pngs_to_numpy(pngs: List[bytes]) -> np.ndarray:
    """Convert a list of png bytes to a numpy array of shape (n, h, w, c)."""
    imgs = []
    for png in pngs:
        img = Image.open(io.BytesIO(png))
        imgs.append(np.array(img))
    return np.stack(imgs, axis=0)'''

NEW = '''def _pngs_to_numpy(pngs: List[bytes]) -> np.ndarray:
    """VAD_IMGFIX: torch-tensor decode — the renderer sends base64(torch.save(tensor)), not PNG.

    Mirrors the UniAD fork's _bytestr_to_numpy; the pydantic Base64Bytes field has already
    base64-decoded, so each item is a torch-serialized (h, w, 3) tensor."""
    imgs = []
    for png in pngs:
        img = torch.load(io.BytesIO(png)).clone()
        imgs.append(img.numpy())
    return np.stack(imgs, axis=0)'''

assert OLD in src, 'expected PIL-based _pngs_to_numpy not found (fork changed?)'
src = src.replace(OLD, NEW, 1)
if 'import torch' not in src:
    src = src.replace('import numpy as np', 'import numpy as np\nimport torch', 1)
open(SRV, 'w').write(src)
print('VAD_IMGFIX_PATCHED')
