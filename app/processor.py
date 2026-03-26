import pandas as pd
from pathlib import Path
from app.validators import validate_required_columns
import json
import asyncio
from app.api_client import fetch_all_devices
import logging

logger = logging.getLogger(__name__)


def process_file(input_file: Path, output_file: Path) -> None:
    df = pd.read_csv(input_file)

    # validate if all columns are existent inside table df
    validate_required_columns(df, ["device_id", "temperature", "status"])

    # convert temperature to numeric
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # create validation flag
    df["has_valid_temperature"] = df["temperature"].notna()

    # create category
    df["temperature_category"] = df["temperature"].apply(categorize_temperature)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # API ENRICHMENT STEP: async operating
    device_ids = df["device_id"].tolist()
    
    try:
        results = asyncio.run(fetch_all_devices(device_ids))
    except Exception as e:
        logger.error(f"API enrichment failed: {e}")
        results=[]

    # cleaning results: by considering cases: success | exception | other(fallback)
    clean_results = []

    for device_id, result in zip(device_ids, results):
        if isinstance(result, Exception):
            clean_results.append({
            "device_id": device_id,
            "api_status": "error",
            "api_response_time": None
        })
        elif isinstance(result, dict):
            clean_results.append({
            "device_id": device_id,
            "api_status": result.get("status"),
            "api_response_time": result.get("response_time")
        })

        else:
        # fallback safety (VERY professional)
            clean_results.append({
            "device_id": device_id,
            "api_status": "unknown",
            "api_response_time": None
        })
            
    api_df=pd.DataFrame(clean_results)

    # merge API data into original dataframe
    df = df.merge(api_df, on="device_id", how="left")
    # clean output regarding time in seconds
    df["api_response_time"] = df["api_response_time"].round(3)

    df.to_csv(output_file, index=False)

    print(f"Processing complete. Output saved to: {output_file}")

    summary = {
        "total_rows": len(df),
        "valid_temperatures": int(df["has_valid_temperature"].sum()),
        "invalid_temperatures": int((~df["has_valid_temperature"]).sum()),
    }

    summary_file = output_file.parent / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=4)


def categorize_temperature(value: float) -> str:
    if pd.isna(value):
        return "invalid"
    if value < 20:
        return "low"
    if value <= 30:
        return "normal"
    return "high"
