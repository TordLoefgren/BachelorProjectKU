import gc
import os
import time
import traceback
from functools import partial
from itertools import tee
from typing import Any, Dict, List, Optional, Tuple

import GPUtil
import pandas as pd
import psutil
from constants import (
    CHUNK_SIZE_BYTES_HEADER,
    DATA_SIZE_BYTES_HEADER,
    DECODE_THROUGHPUT_MB_S_HEADER,
    DESERIALIZE_THROUGHPUT_MB_S_HEADER,
    ENCODE_THROUGHPUT_MB_S_HEADER,
    ENCODING_LIBRARY_HEADER,
    ERROR_CORRECTION_LEVEL_HEADER,
    FRAMES_COUNT_HEADER,
    MAX_WORKERS_HEADER,
    MP4_FILE,
    QR_VERSION_HEADER,
    READ_VIDEO_THROUGHPUT_MB_S_HEADER,
    ROUNDTRIP_SUCCESS_HEADER,
    SERIALIZE_THROUGHPUT_MB_S_HEADER,
    TIME_DECODE_HEADER,
    TIME_DESERIALIZE_HEADER,
    TIME_ENCODE_HEADER,
    TIME_READ_VIDEO_HEADER,
    TIME_SERIALIZE_HEADER,
    TIME_TOTAL_HEADER,
    TIME_WRITE_VIDEO_HEADER,
    TOTAL_THROUGHPUT_MB_S_HEADER,
    VIDEO_SIZE_MB_HEADER,
    WRITE_VIDEO_THROUGHPUT_MB_S_HEADER,
    BenchmarkParameters,
)
from src.base import EncodingConfiguration
from src.constants import BYTE_TO_MB, MILLISECONDS_PER_SECOND, SEED
from src.enums import QREncodingLibrary, QRErrorCorrectionLevel
from src.performance import measure_task_performance
from src.qr_configuration import QREncodingConfiguration
from src.qr_encoding import qr_version_for_size
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.qr_video_encoder import QRVideoEncoder
from src.utils import generate_random_bytes, remove_file, try_get_iter_count
from tqdm import tqdm


def create_encoder_roundtrip_benchmarks(
    file_name: str,
    benchmark_parameters: BenchmarkParameters = BenchmarkParameters.all(),
    save_every_n: int = 12,
    eager: bool = False,
) -> None:

    total_runs = benchmark_parameters.get_total_runs()

    # Load existing progress if it already exists.
    if os.path.exists(file_name):
        existing_df = pd.read_csv(file_name)
        existing_entries = existing_df.to_dict(orient="records")
        completed_entries = {
            (
                entry[ENCODING_LIBRARY_HEADER],
                entry[ERROR_CORRECTION_LEVEL_HEADER],
                entry[MAX_WORKERS_HEADER] if entry[MAX_WORKERS_HEADER] > 1 else 0,
                entry[DATA_SIZE_BYTES_HEADER],
                entry[CHUNK_SIZE_BYTES_HEADER],
            )
            for entry in existing_entries
        }
    else:
        existing_entries = []
        completed_entries = set()

    entries = existing_entries.copy()
    unsaved_entries = []

    with tqdm(total=total_runs, desc="Benchmarking") as progress_bar:
        progress_bar.update(len(completed_entries))

        for qr_encoding_library in benchmark_parameters.qr_encoding_libraries:
            for error_correction_level in benchmark_parameters.error_correction_levels:
                max_payload_size = QRErrorCorrectionLevel.to_max_bytes(
                    error_correction_level
                )
                chunk_sizes_bytes = benchmark_parameters.get_chunk_sizes(
                    max_payload_size=max_payload_size
                )

                for (
                    max_workers,
                    data_size,
                ) in benchmark_parameters.get_worker_data_pairs():
                    pool_size = max_workers if max_workers > 1 else 0
                    data = generate_random_bytes(data_size, SEED)
                    enable_multiprocessing = pool_size > 0

                    for chunk_size_bytes in chunk_sizes_bytes:
                        key = (
                            qr_encoding_library.name.title(),
                            error_correction_level.name.title(),
                            pool_size,
                            len(data),
                            chunk_size_bytes,
                        )

                        configuration = QREncodingConfiguration(
                            enable_multiprocessing=enable_multiprocessing,
                            error_correction=error_correction_level,
                            chunk_size=chunk_size_bytes,
                            max_workers=pool_size,
                            qr_encoding_library=qr_encoding_library,
                        )

                        if key in completed_entries:
                            continue

                        try:

                            if eager:
                                (
                                    time_serialize_ms,
                                    time_deserialize_ms,
                                    time_encode_ms,
                                    time_decode_ms,
                                    time_write_video_ms,
                                    time_read_video_ms,
                                    time_total_ms,
                                    frames_count,
                                    video_size_bytes,
                                    roundtrip_success,
                                    snapshots,
                                ) = _benchmark_full_pipeline(
                                    data=data, configuration=configuration
                                )
                            else:
                                (
                                    time_encode_ms,
                                    time_decode_ms,
                                    time_total_ms,
                                    frames_count,
                                    video_size_bytes,
                                    roundtrip_success,
                                    snapshots,
                                ) = _benchmark_encoder_roundtrip(
                                    data=data, configuration=configuration
                                )

                            entry = _create_entry(
                                qr_encoding_library=qr_encoding_library,
                                version=qr_version_for_size(
                                    chunk_size_bytes,
                                    error_correction_level,
                                ),
                                error_correction_level=error_correction_level,
                                max_workers=max_workers,
                                data=data,
                                chunk_size_bytes=chunk_size_bytes,
                                video_size_bytes=video_size_bytes,
                                frames_count=frames_count,
                                time_encode_ms=time_encode_ms,
                                time_decode_ms=time_decode_ms,
                                time_total_ms=time_total_ms,
                                roundtrip_success=roundtrip_success,
                                time_serialize_ms=(
                                    time_serialize_ms if eager else None
                                ),
                                time_deserialize_ms=(
                                    time_deserialize_ms if eager else None
                                ),
                                time_write_video_ms=(
                                    time_write_video_ms if eager else None
                                ),
                                time_read_video_ms=(
                                    time_read_video_ms if eager else None
                                ),
                            )

                            entry.update(snapshots)

                            entries.append(entry)
                            unsaved_entries.append(entry)
                            remove_file(MP4_FILE)

                        except Exception as e:
                            print(f"Error during run {key}: {e}")
                            traceback.print_exc()

                        progress_bar.update(1)

                        # Save every N entries.
                        if len(unsaved_entries) >= save_every_n:
                            _save_benchmarks_as_csv(
                                unsaved_entries, file_name, final_save=False
                            )
                            unsaved_entries.clear()
                            gc.collect()

    # Final save.
    if unsaved_entries:
        _save_benchmarks_as_csv(unsaved_entries, file_name)


def _benchmark_full_pipeline(
    data: bytes, configuration: QREncodingConfiguration
) -> Tuple[
    float, float, float, float, float, float, float, int, int, bool, Dict[str, Any]
]:

    pipeline = create_qr_video_encoding_pipeline()
    snapshots = {}

    start_total = time.perf_counter()

    # 1. Serialize.
    start_serialize = time.perf_counter()
    header_with_length = EncodingConfiguration.serialize_with_length_prefix(
        configuration
    )
    header_serialized = pipeline.serializer.serialize(header_with_length)
    data_serialized = pipeline.serializer.serialize(data)
    time_serialize_ms = (
        time.perf_counter() - start_serialize
    ) * MILLISECONDS_PER_SECOND
    snapshots.update(_capture_step_snapshot("Serialize"))

    # 2. Encode (lazy -> eager).
    start_encode = time.perf_counter()
    header_frames = list(
        pipeline.encoder.encode(header_serialized, configuration, True)
    )
    data_frames = list(pipeline.encoder.encode(data_serialized, configuration, False))
    all_frames = header_frames + data_frames
    time_encode_ms = (time.perf_counter() - start_encode) * MILLISECONDS_PER_SECOND
    snapshots.update(_capture_step_snapshot("Encode"))

    # 3. Write video.
    time_write_video_ms = measure_task_performance(
        partial(pipeline.video_handler.write, iter(all_frames), MP4_FILE, configuration)
    )
    snapshots.update(_capture_step_snapshot("Write Video"))

    # 4. Read video.
    frames, time_read_video_ms = measure_task_performance(
        partial(pipeline.video_handler.read, MP4_FILE, configuration)
    )
    frames, frames_for_count = tee(frames)
    snapshots.update(_capture_step_snapshot("Read Video"))

    # 5. Decode (lazy -> eager).
    start_decode = time.perf_counter()
    header_frame = next(frames)
    raw_header_serialized = pipeline.encoder.decode([header_frame], None)
    raw_header = pipeline.serializer.deserialize(raw_header_serialized)
    configuration = EncodingConfiguration.deserialize_with_length_prefix(raw_header)
    raw_data_serialized = pipeline.encoder.decode(list(frames), configuration)
    time_decode_ms = (time.perf_counter() - start_decode) * MILLISECONDS_PER_SECOND
    snapshots.update(_capture_step_snapshot("Decode"))

    # 6. Deserialize.
    result, time_deserialize_ms = measure_task_performance(
        partial(pipeline.serializer.deserialize, raw_data_serialized)
    )
    snapshots.update(_capture_step_snapshot("Deserialize"))

    # Total.
    time_total_ms = (time.perf_counter() - start_total) * MILLISECONDS_PER_SECOND

    video_size_bytes = os.path.getsize(MP4_FILE)

    frames_count = 1 + sum(1 for _ in frames_for_count)

    del header_frame, data_frames, all_frames, raw_data_serialized, raw_header
    gc.collect()

    return (
        time_serialize_ms,
        time_deserialize_ms,
        time_encode_ms,
        time_decode_ms,
        time_write_video_ms,
        time_read_video_ms,
        time_total_ms,
        frames_count,
        video_size_bytes,
        data == result,
        snapshots,
    )


def _benchmark_encoder_roundtrip(
    data: bytes, configuration: QREncodingConfiguration
) -> Tuple[float, float, float, int, int, bool, Dict[str, Any]]:

    qr_video_encoder = QRVideoEncoder(configuration)

    snapshots = {}

    # Encoding.
    frames, time_encode_ms = measure_task_performance(
        partial(qr_video_encoder.encode, data, MP4_FILE)
    )

    # Decoding.
    result, time_decode_ms = measure_task_performance(
        partial(qr_video_encoder.decode, MP4_FILE)
    )
    snapshots.update(_capture_step_snapshot("Encode"))

    # Total.
    time_total_ms = time_encode_ms + time_decode_ms
    snapshots.update(_capture_step_snapshot("Decode"))

    video_size_bytes = os.path.getsize(MP4_FILE)

    _, frames_count, _ = try_get_iter_count(frames)

    return (
        time_encode_ms,
        time_decode_ms,
        time_total_ms,
        frames_count,
        video_size_bytes,
        data == result,
        snapshots,
    )


def _create_entry(
    qr_encoding_library: QREncodingLibrary,
    version: int,
    error_correction_level: QRErrorCorrectionLevel,
    max_workers: int,
    data: bytes,
    chunk_size_bytes: int,
    video_size_bytes: int,
    frames_count: int,
    time_encode_ms: float,
    time_decode_ms: float,
    time_total_ms: float,
    roundtrip_success: bool,
    time_serialize_ms: Optional[float] = None,
    time_deserialize_ms: Optional[float] = None,
    time_write_video_ms: Optional[float] = None,
    time_read_video_ms: Optional[float] = None,
) -> Dict[str, Any]:

    data_size_bytes = len(data)
    data_size_mb = data_size_bytes * BYTE_TO_MB
    video_size_mb = video_size_bytes * BYTE_TO_MB

    return {
        ENCODING_LIBRARY_HEADER: qr_encoding_library.name.title(),
        QR_VERSION_HEADER: version,
        ERROR_CORRECTION_LEVEL_HEADER: error_correction_level.name.title(),
        MAX_WORKERS_HEADER: max_workers,
        DATA_SIZE_BYTES_HEADER: data_size_bytes,
        CHUNK_SIZE_BYTES_HEADER: chunk_size_bytes,
        FRAMES_COUNT_HEADER: frames_count,
        VIDEO_SIZE_MB_HEADER: round(video_size_mb, 2),
        TIME_SERIALIZE_HEADER: time_serialize_ms,
        TIME_DESERIALIZE_HEADER: time_deserialize_ms,
        TIME_ENCODE_HEADER: time_encode_ms,
        TIME_DECODE_HEADER: time_decode_ms,
        TIME_WRITE_VIDEO_HEADER: time_write_video_ms,
        TIME_READ_VIDEO_HEADER: time_read_video_ms,
        TIME_TOTAL_HEADER: time_total_ms,
        ROUNDTRIP_SUCCESS_HEADER: roundtrip_success,
        SERIALIZE_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_serialize_ms * MILLISECONDS_PER_SECOND
            if time_serialize_ms is not None and time_serialize_ms > 0
            else None
        ),
        DESERIALIZE_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_deserialize_ms * MILLISECONDS_PER_SECOND
            if time_deserialize_ms is not None and time_deserialize_ms > 0
            else None
        ),
        WRITE_VIDEO_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_write_video_ms * MILLISECONDS_PER_SECOND
            if time_write_video_ms is not None and time_write_video_ms > 0
            else None
        ),
        READ_VIDEO_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_read_video_ms * MILLISECONDS_PER_SECOND
            if time_read_video_ms is not None and time_read_video_ms > 0
            else None
        ),
        ENCODE_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_encode_ms * MILLISECONDS_PER_SECOND
            if time_encode_ms > 0
            else None
        ),
        DECODE_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_decode_ms * MILLISECONDS_PER_SECOND
            if time_decode_ms > 0
            else None
        ),
        TOTAL_THROUGHPUT_MB_S_HEADER: (
            data_size_mb / time_total_ms * MILLISECONDS_PER_SECOND
            if time_total_ms > 0
            else None
        ),
    }


def _save_benchmarks_as_csv(
    entries: List[Dict[str, Any]], file_name: str, final_save: bool = True
) -> None:
    df = pd.DataFrame(entries)

    df.to_csv(
        file_name,
        mode="a",
        header=not os.path.exists(file_name),
        index=False,
    )

    if final_save:
        print(f"Benchmarks saved as {file_name}.")
    else:
        print(f"Progress checkpoint saved to '{file_name}'.")

    del df
    gc.collect()


def _capture_step_snapshot(step_name: str) -> Dict[str, Any]:
    cpu = psutil.cpu_percent(interval=0.0)
    mem_pct = psutil.virtual_memory().percent
    gpus = GPUtil.getGPUs()
    gpu_pct = (gpus[0].load * 100) if gpus else None

    return {
        f"{step_name} CPU Usage (%)": round(cpu, 2),
        f"{step_name} Memory Usage (%)": round(mem_pct, 2),
        f"{step_name} GPU Usage (%)": (
            round(gpu_pct, 2) if gpu_pct is not None else None
        ),
    }
