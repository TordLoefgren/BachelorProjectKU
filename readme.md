# Bachelor Project

### Data Storage through Visual Encoding

This repository is part of my third-year Computer Science bachelor project at the University of Copenhagen.



#### Introduction

The purpose of this project was to explore the use of visual data encoding as a method for storing arbitrary
binary data. The process should be reversible and should include considerations on payload capacity, versioning, and error tolerance. 

Another focus was on performance and measuring performance through benchmarks.



#### Demo: 

This demo reads a file, encodes it as a QR video, and decodes it back to verify roundtrip success.

```python
from src.qr_configuration import QREncodingConfiguration
from src.qr_video_encoder import QRVideoEncoder
from src.utils import read_file_as_binary, write_file_as_binary

# Read file as binary.
input_data = read_file_as_binary("input.txt")

# Create configuration and encoder.
config = QREncodingConfiguration()
encoder = QRVideoEncoder(config)

# Encode and decode in a single step.
result = encoder.roundtrip(input_data, file_path="demo_video.mp4")

if result.is_valid:
    # Create a 1:1 copy of the input text.
    write_file_as_binary(result.value, "output.txt")
else:
    print("Decoding failed:", result.exception)
```

<details>
  <summary>Click to show sample video output (⚠️ Warning: Photosensitive Content) </summary>
  <img src="/demo.gif" alt="Demo" />
</details>



#### Tests
To run the unit test suite, navigate to the ```Project``` directory, and write ```"python -m unittest discover tests"``` in the console.
