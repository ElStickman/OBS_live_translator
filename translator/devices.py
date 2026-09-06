from __future__ import annotations

import sys
from dataclasses import asdict, dataclass

import sounddevice as sd


@dataclass(frozen=True)
class AudioSource:
    backend: str
    device: int
    name: str
    channels: int
    sample_rate: int

    def as_dict(self) -> dict[str, str | int]:
        return asdict(self)


def list_audio_sources() -> list[AudioSource]:
    sources: list[AudioSource] = []
    for index, device in enumerate(sd.query_devices()):
        channels = int(device["max_input_channels"])
        if channels > 0:
            sources.append(
                AudioSource(
                    backend="sounddevice",
                    device=index,
                    name=f"{device['name']} [{sd.query_hostapis(device['hostapi'])['name']}]",
                    channels=channels,
                    sample_rate=round(device["default_samplerate"]),
                )
            )

    if sys.platform == "win32":
        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            return sources

        with pyaudio.PyAudio() as audio:
            for device in audio.get_loopback_device_info_generator():
                sources.append(
                    AudioSource(
                        backend="wasapi_loopback",
                        device=int(device["index"]),
                        name=f"{device['name']} [WASAPI loopback]",
                        channels=int(device["maxInputChannels"]),
                        sample_rate=round(device["defaultSampleRate"]),
                    )
                )
    return sources


def print_audio_sources() -> None:
    for source in list_audio_sources():
        print(
            f"{source.backend:16} {source.device:3}  "
            f"{source.channels} ch  {source.sample_rate:5} Hz  {source.name}"
        )
