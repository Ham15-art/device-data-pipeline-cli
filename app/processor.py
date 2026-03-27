import pandas as pd
from pathlib import Path
from app.validators import validate_required_columns
import json
import asyncio
from app.api_client import fetch_all_devices
import logging
from app.models import DeviceResponse


logger = logging.getLogger(__name__)


def process_file(input_file: Path, output_file: Path) -> None:
    df = pd.read_csv(input_file)

    # validate if all required columns are existent inside dataframe df
    validate_required_columns(df, ["device_id", "temperature", "status"])

    # convert temperature to numeric
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # create validation flag
    df["has_valid_temperature"] = df["temperature"].notna()

    # create category
    df["temperature_category"] = df["temperature"].apply(categorize_temperature)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # API ENRICHMENT starts here: asynchronous running
    device_ids = df["device_id"].tolist()

    try:
        results: list[DeviceResponse] = asyncio.run(fetch_all_devices(device_ids))
    except Exception:
        logger.error(f"API enrichment failed: ", exc_info=True)
        results = []

    if not results:
        logger.warning("No API results received, filling defaults")
        results = [
            DeviceResponse(device_id=d, data=None, error="no_data", api_latency=0.0, queue_time=0.0, end_to_end_latency=0.0)
            for d in device_ids
        ]

    # cleaning results: by considering these cases: success | exception/error , in a pythonic way.
    clean_results: list[dict[str, object]] = [
        {
            "device_id": r.device_id,
            "api_status": "error" if r.error is not None else "success",
            "api_latency": r.api_latency,
            "queue_time": r.queue_time,
            "end_to_end_latency": r.end_to_end_latency,
        }
        for r in results
    ]

    # format clean results as data frame
    api_df = pd.DataFrame(clean_results)

    # merge API data into original dataframe
    df = df.merge(api_df, on="device_id", how="left")

    # round api response time
    df["api_latency"] = df["api_latency"].astype(float).round(3)
    df["queue_time"] = df["queue_time"].astype(float).round(3)
    df["end_to_end_latency"] = df["end_to_end_latency"].astype(float).round(3)

    # create csv file (output)
    df.to_csv(output_file, index=False)

    logger.info(f"Processing complete. Output saved to: {output_file}")

    # make summary of successes and errors
    success_count = sum(1 for r in results if r.error is None)
    error_count = sum(1 for r in results if r.error is not None)
    avg_api_latency = round(sum(r.api_latency for r in results) / len(results), 3)
    avg_queue_time = round(sum(r.queue_time for r in results) / len(results), 3)
    avg_end_to_end_latency = round(sum(r.end_to_end_latency for r in results) / len(results), 3)
    summary = {
        "total_rows": len(df),
        "valid_temperatures": int(df["has_valid_temperature"].sum()),
        "invalid_temperatures": int((~df["has_valid_temperature"]).sum()),
        "api_success": success_count,
        "api_errors": error_count,
        "avg_api_latency": avg_api_latency,
        "avg_queue_time" : avg_queue_time,
        "avg_end_to_end_latency" : avg_end_to_end_latency
    }

    summary_file = output_file.parent / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=4)


# function that categorizes temoperature entries inot low|normal|high or invalid
def categorize_temperature(value: float) -> str:
    if pd.isna(value):
        return "invalid"
    if value < 20:
        return "low"
    if value <= 30:
        return "normal"
    return "high"
