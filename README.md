# Excel Workflow CLI with API Enrichment

What this project does:
Processes CSV device data, validates it, categorizes temperature values, and enriches each device with external API data asynchronously.

Architecture:
app/
├── main.py           # CLI entry point
├── processor.py      # core business logic
├── api_client.py     # async API communication
├── validators.py     # input validation
├── models.py         # data structures (pydantic-ready)

Features:
CSV processing with pandas
Data validation
Temperature categorization
Async API calls (aiohttp)
JSON summary export
CLI interface

How to run:
pip install -r requirements.txt
python -m app.main \
  --input data/input/devices.csv \
  --output data/output/result.csv

Example input/output:
input: input.csv
output: output.csv and summary.json

Tech stack:
Python
pandas
asyncio
aiohttp