"""Use soundfile for torchaudio I/O on PyTorch 2.11 (torchcodec not required)."""

from __future__ import annotations

import soundfile as sf
import torch
import torchaudio


def _save_wav(
    uri,
    src: torch.Tensor,
    sample_rate: int,
    channels_first: bool = True,
    **_kwargs,
) -> None:
    audio = src.detach().cpu()
    if channels_first and audio.ndim == 2:
        audio = audio.transpose(0, 1)
    sf.write(str(uri), audio.numpy(), int(sample_rate))


def _load_wav(uri, frame_offset: int = 0, num_frames: int = -1, normalize: bool = True, **_kwargs):
    data, sample_rate = sf.read(
        str(uri),
        dtype="float32",
        always_2d=True,
        frames=num_frames if num_frames >= 0 else -1,
        start=frame_offset,
    )
    tensor = torch.from_numpy(data.T.copy())
    if normalize:
        tensor = torchaudio.functional.normalize(tensor, norm="inf", eps=1e-8)
    return tensor, int(sample_rate)


torchaudio.save = _save_wav
torchaudio.load = _load_wav