# Data Storage Through Visual Encoding

*A reversible QR-video encoding pipeline for binary data.*

This repository contains the software prototype developed for **Data Storage Through Visual Encoding**, my third-year BSc project in Computer Science at the University of Copenhagen.

The system encodes binary data as sequences of QR-code video frames and decodes the video back into the original data. It was developed to investigate pipeline architecture, reversibility, multiprocessing, memory usage, throughput, and scalability.

The repository contains the implementation and benchmark artifacts. The accompanying bachelor report is not included.


## Motivation

The project originated from the question of whether QR codes could be used as an unconventional storage medium in video. Their built-in error correction made them particularly interesting, as it could potentially help encoded data survive lossy video compression and transcoding.


## Architecture

The system uses a symmetric, modular pipeline:

```text
serialize -> encode -> write video -> read video -> decode -> deserialize
```

Each stage has a corresponding inverse operation, enabling direct end-to-end validation.

Binary payloads are Base64-serialized before QR encoding to avoid limitations encountered in the decoding libraries. Data is processed lazily and in chunks where possible to reduce peak memory usage, while CPU-bound QR generation and decoding are parallelized using multiprocessing.


## What the Project Demonstrates

- Symmetric and reversible pipeline design
- Modular layers with unit and end-to-end testing
- Reliable round trips of binary payloads within tested configurations
- Multiprocessing for CPU-bound workloads
- Lazy and chunked data processing
- Benchmarking of throughput, CPU usage, memory usage, and scalability
- Analysis of payload size, QR version, error correction, and chunking trade-offs


## Results and Limitations

- QR generation and image processing were the primary performance bottlenecks
- Multiprocessing improved throughput and CPU utilization but did not remove the bottleneck
- Strong scaling was useful for approximately the first ten workers before diminishing returns
- Weak scaling deteriorated as both workload and worker count increased
- Data-to-video throughput was approximately 0.01–0.06 MB/s, depending on configuration
- Best-case video-to-data throughput was approximately 0.5 MB/s
- Inputs up to approximately 1 MB were processed reliably on the tested desktop hardware; larger inputs worked but became increasingly slow
- Benchmarking exposed significant memory issues, leading to a refactor toward lazy, on-demand processing
- Lazy processing reduced memory usage but introduced behavioral coupling between image generation and video processing, complicating some isolated benchmarks
- The modular architecture improved testing and extensibility but was more general than required for a prototype using only QR-code encoding
- Real-world viability would require further investigation of serialization, alternative encodings, video compression, and platform-specific transcoding

The resulting system is a reliable proof of concept and a foundation for further experimentation, not a production-ready storage solution.


## Future Work

The project uses general-purpose QR libraries for sustained, high-volume frame generation—a workload substantially different from conventional one-code-at-a-time use.

A useful next step would be to profile QR matrix construction, image rasterization, memory transfer, and video encoding separately. Depending on the results, QR generation could then be moved to a batched native implementation or accelerated on the GPU.

Other areas for investigation include alternative serialization, visual encoding methods, video compression, and platform-specific transcoding.


## Repository Structure

```text
Project/
├── src/            # Pipeline implementation
├── tests/          # Unit and round-trip tests
├── benchmarks/     # Benchmark scripts and recorded data
└── main.py         # Example entry point

demo.gif            # Example QR-video output
requirements.txt    # Python dependencies
readme.md           # Project documentation
```


## Demo

The following example performs a complete data-to-video-to-data round trip:

```python
from src.qr_configuration import QREncodingConfiguration
from src.qr_video_encoder import QRVideoEncoder
from src.utils import read_file_as_binary, write_file_as_binary

input_data = read_file_as_binary("input.txt")

encoder = QRVideoEncoder(
    QREncodingConfiguration(verbose=True)
)

result = encoder.roundtrip(
    input_data,
    file_path="demo_video.mp4",
)

if result.is_valid:
    write_file_as_binary(result.value, "output.txt")
    print("Success")
else:
    print("Decoding failed:", result.exception)
```

<details>
  <summary>Show sample output — warning: rapidly flashing QR-code frames</summary>

  <img src="./demo.gif" alt="Example output from the QR-video encoding pipeline" />
</details>


## Getting Started

Install the dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
```

Run the example:

```bash
cd Project
python main.py
```

Run the test suite:

```bash
python -m unittest discover tests
```
