# Data Storage Through Visual Encoding

**Data Storage Through Visual Encoding** is an experimental sandbox project developed as part of my third-year Computer Science bachelor thesis at the University of Copenhagen.

It explores how a **reliable and reversible pipeline** can be constructed for storing arbitrary binary data by converting it into a sequence of QR codes embedded in video frames and then decoding that video back to the original data.

This project is intended as a learning and research prototype rather than a production-ready storage system.



## Project Status

This project is a research prototype and proof-of-concept.

The primary goal is to explore system architecture, reversibility, and empirical analysis of a QR–video encoding pipeline.

The project prioritizes:

- Designing a clean, symmetric, and modular pipeline  
- Making bottlenecks observable  
- Measuring scaling behavior and resource usage  

Performance optimization of individual stages is considered outside the main scope of the project and is deliberately deferred in favor of benchmarking and empirical analysis.



## What This Project Demonstrates

- Designing a symmetric, reversible data pipeline  
- Modular architecture with clearly separated layers  
- Handling arbitrary binary data end-to-end  
- Multiprocessing for CPU-bound workloads  
- Lazy evaluation and chunked processing of data  
- Benchmark-driven identification of bottlenecks  
- Strong and weak scaling experiments  
- Making informed architectural trade-offs  



## Results Summary

- End-to-end encoding and decoding is fully reversible  
- The pipeline reliably round-trips arbitrary binary data  
- Dominant bottleneck: QR generation and image processing  
- Multiprocessing improves throughput but does not remove the primary bottleneck  
- Experiments show that QR image generation dominates runtime even when parallelized
- Practical behavior on typical desktop hardware:
  - Reliable up to ~1 MB inputs  
  - Larger inputs work but become increasingly slow  
  - End-to-end throughput roughly ~0.01–0.06 MB/s depending on configuration  



## Design Rationale

The system is intentionally designed around a symmetric, modular pipeline:

```
serialize -> encode -> write video -> read video -> decode -> deserialize
```

Each stage has an inverse operation, enabling direct round-trip validation. 

Pipeline stages are evaluated lazily where possible, allowing data to be processed incrementally in chunks.

Multiprocessing is used to improve throughput, but the project does not does not optimize the QR generation or image processing algorithms directly.

Rather than focusing on optimizations of individual stages directly, the project focuses on:

- Making bottlenecks visible  
- Measuring scaling behavior  
- Exploring trade-offs between payload size, error correction, and chunking  



## Repository Overview

The repository is organized around three main areas:

```
src/            # Core pipeline implementation
tests/          # Unit tests and round-trip validation tests
benchmarks/     # Benchmark scripts and recorded benchmark data
```


### src/

Contains the implementation of the QR-video encoding pipeline:

- Serialization and deserialization  
- QR encoding and decoding  
- Video writing and reading  
- Configuration system  

This is where the architectural ideas of a symmetric, modular pipeline are implemented.

### tests/

Unit tests and integration-style tests that validate:

- Individual pipeline layers  
- End-to-end round-trip correctness  

Tests focus primarily on correctness rather than performance.

### benchmarks/

Scripts and datasets used to measure:

- Throughput  
- CPU usage  
- Memory usage  
- Scaling behavior  

Benchmarks are intended to expose bottlenecks and performance trends, not to present an optimized solution.



## Demo

The example below reads a text file as bytes, encodes it into a QR code video, and then decodes the video to produce an output file.  
This round-trip verifies that the decoded result matches the original input data:

```python
from src.qr_configuration import QREncodingConfiguration
from src.qr_video_encoder import QRVideoEncoder
from src.utils import read_file_as_binary, write_file_as_binary

# Read file as binary.
input_data = read_file_as_binary("input.txt")

# Create configuration and encoder.
config = QREncodingConfiguration(
    verbose=True  # Print pipeline stages and progress
)
encoder = QRVideoEncoder(config)

# Encode and decode in a single step.
result = encoder.roundtrip(input_data, file_path="demo_video.mp4")

if result.is_valid:
    # Create a 1:1 copy of the input text.
    print("Success")
    write_file_as_binary(result.value, "output.txt")
else:
    print("Decoding failed:", result.exception)
```

<details>
  <summary>Click to show sample video output (⚠️ Warning: Photosensitive Content) </summary>
  <img src="/demo.gif" alt="Demo" />
</details>


### Getting Started

Make sure you have Python 3 and the required dependencies installed. You can install all dependencies using the provided requirements file:

```pip install -r requirements.txt```

To run the unit test suite, navigate to the Project directory and execute:

```python -m unittest discover tests```
