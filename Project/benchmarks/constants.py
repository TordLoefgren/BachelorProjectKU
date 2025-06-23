from dataclasses import dataclass
from typing import List, Tuple

from src.enums import QREncodingLibrary, QRErrorCorrectionLevel

ENCODING_LIBRARY_HEADER = "Encoding Library"
QR_VERSION_HEADER = "Version"
ERROR_CORRECTION_LEVEL_HEADER = "Error Correction Level"
MAX_WORKERS_HEADER = "Max Workers"
CHUNK_SIZE_BYTES_HEADER = "Chunk Size (bytes)"
DATA_SIZE_BYTES_HEADER = "Data Size (bytes)"
FRAMES_COUNT_HEADER = "Frames Count"
VIDEO_SIZE_MB_HEADER = "Video Size (MB)"
TIME_SERIALIZE_HEADER = "Time Serialize (ms)"
TIME_DESERIALIZE_HEADER = "Time Deserialize (ms)"
TIME_ENCODE_HEADER = "Time Encode (ms)"
TIME_DECODE_HEADER = "Time Decode (ms)"
TIME_WRITE_VIDEO_HEADER = "Time Write Video (ms)"
TIME_READ_VIDEO_HEADER = "Time Read Video (ms)"
TIME_TOTAL_HEADER = "Time Total (ms)"
TIME_FORWARD_PIPELINE_HEADER = "Time Forward Pipeline (ms)"
TIME_BACKWARD_PIPELINE_HEADER = "Time Backward Pipeline (ms)"
ENCODE_THROUGHPUT_MB_S_HEADER = "Encode Throughput (MB/s)"
DECODE_THROUGHPUT_MB_S_HEADER = "Decode Throughput (MB/s)"
SERIALIZE_THROUGHPUT_MB_S_HEADER = "Serialize Throughput (MB/s)"
DESERIALIZE_THROUGHPUT_MB_S_HEADER = "Deserialize Throughput (MB/s)"
WRITE_VIDEO_THROUGHPUT_MB_S_HEADER = "Write Video Throughput (MB/s)"
READ_VIDEO_THROUGHPUT_MB_S_HEADER = "Read Video Throughput (MB/s)"
TOTAL_THROUGHPUT_MB_S_HEADER = "Total Throughput (MB/s)"
ROUNDTRIP_SUCCESS_HEADER = "Roundtrip Success"

BENCHMARKS_ALL_EAGER_PATH = "data/benchmark_all_eager.csv"
BENCHMARKS_ALL_EAGER_WITH_RESULT_PATH = "data/benchmark_all_eager_with_result.csv"
BENCHMARKS_STRONG_SCALING_EAGER_PATH = "data/benchmark_strong_scaling_eager.csv"
BENCHMARKS_STRONG_SCALING_LAZY_PATH = "data/benchmark_strong_scaling_lazy.csv"
BENCHMARKS_STRONG_SCALING_LAZY_WITH_RESULT_PATH = (
    "data/benchmark_strong_scaling_lazy_with_result.csv"
)
BENCHMARKS_WEAK_SCALING_EAGER_PATH = "data/benchmark_weak_scaling_eager.csv"
BENCHMARKS_WEAK_SCALING_LAZY_PATH = "data/benchmark_weak_scaling_lazy.csv"
BENCHMARKS_WEAK_SCALING_LAZY_WITH_RESULT_PATH = (
    "data/benchmark_weak_scaling_lazy_with_result.csv"
)
MP4_FILE = "temp.mp4"
MB = 1_000_000
KB = 1_000

ERROR_CORRECTION_LEVELS = [
    QRErrorCorrectionLevel.L,
    QRErrorCorrectionLevel.M,
    QRErrorCorrectionLevel.Q,
    QRErrorCorrectionLevel.H,
]
CHUNK_DIVISORS = [1, 2, 4]
MAX_WORKERS = [1, 2, 4, 6, 8, 10, 12, 14, 16]
DATA_SIZES = [1_000, 10_000, 100_000, MB]
QR_ENCODING_LIBRARIES = [QREncodingLibrary.SEGNO, QREncodingLibrary.QRCODE]


@dataclass
class BenchmarkParameters:
    chunk_divisors: List[int]
    data_sizes: List[int]
    error_correction_levels: List[QRErrorCorrectionLevel]
    max_workers: List[int]
    qr_encoding_libraries: List[QREncodingLibrary]
    use_weak_scaling: bool = False

    @classmethod
    def all(cls) -> "BenchmarkParameters":
        return BenchmarkParameters(
            chunk_divisors=CHUNK_DIVISORS,
            data_sizes=DATA_SIZES,
            error_correction_levels=ERROR_CORRECTION_LEVELS,
            max_workers=MAX_WORKERS,
            qr_encoding_libraries=QR_ENCODING_LIBRARIES,
        )

    @classmethod
    def strong_scaling(cls) -> "BenchmarkParameters":
        return BenchmarkParameters(
            chunk_divisors=[1],
            data_sizes=[MB],
            error_correction_levels=[QRErrorCorrectionLevel.L],
            max_workers=[1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24],
            qr_encoding_libraries=QR_ENCODING_LIBRARIES,
        )

    @classmethod
    def weak_scaling(cls, multiplier_kb: int = 250) -> "BenchmarkParameters":
        max_workers = [1, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
        data_sizes = [KB * multiplier_kb * n_worker for n_worker in max_workers]

        return BenchmarkParameters(
            chunk_divisors=[1],
            data_sizes=data_sizes,
            error_correction_levels=[QRErrorCorrectionLevel.L],
            max_workers=max_workers,
            qr_encoding_libraries=QR_ENCODING_LIBRARIES,
            use_weak_scaling=True,
        )

    def get_chunk_sizes(self, max_payload_size: int) -> List[int]:
        return [max_payload_size // divisor for divisor in self.chunk_divisors]

    def get_worker_data_pairs(self) -> List[Tuple[int, int]]:
        if self.use_weak_scaling:
            return list(zip(self.max_workers, self.data_sizes))
        else:
            return [
                (workers, data_size)
                for workers in self.max_workers
                for data_size in self.data_sizes
            ]

    def get_total_runs(self) -> int:
        worker_data_pair_count = (
            len(self.data_sizes)
            if self.use_weak_scaling
            else len(self.max_workers) * len(self.data_sizes)
        )

        return (
            len(self.qr_encoding_libraries)
            * len(self.error_correction_levels)
            * len(self.chunk_divisors)
            * worker_data_pair_count
        )
