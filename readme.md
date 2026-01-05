### Data Storage through Visual Encoding

**Data Storage through Visual Encoding** is an experimental sandbox project developed as part of my third-year Computer Science bachelor thesis at the University of Copenhagen. 

It explores storing binary data by converting it into a sequence of QR codes that are embedded in video frames and then decoding that video back to the original data. While fully functional, this project was built as a proof-of-concept for research and learning, not as a production-ready utility library. 

Key features include:
- **Modular pipeline design**: The encoding/decoding workflow is composed of interchangeable modules (for data serialization, QR code generation, video handling, etc.), making it easy to adjust or extend each stage.
- **Reversible process**: The pipeline is symmetric – data encoded into a QR code video can be decoded back losslessly to the original input, ensuring a 1:1 round-trip.
- **Performance benchmarking**: Includes tools to measure encoding/decoding speed and evaluate how different configurations affect data throughput and reliability.



### Demo: 

The example below reads a text file as bytes, encodes it into a QR code video, and then decodes the video to produce an output file. This round-trip verifies that the decoded result matches the original input data:

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
