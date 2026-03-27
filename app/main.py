from pathlib import Path
from app.processor import process_file
import argparse
import os
from app.logger import setup_logger
import logging


def main() -> None:
    setup_logger()
    logger = logging.getLogger(__name__)
    logger.info("Starting program...")

    parser = argparse.ArgumentParser(
        description="Process a device CSV file (path flexible)"
    )
    parser.add_argument("--input", required=True, help="path to csv file as input")
    parser.add_argument("--output", required=True, help="path to csv file as output")

    args = parser.parse_args()

    input_file = Path(args.input)
    output_file = Path(args.output)

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return

    try:
        process_file(input_file, output_file)
        print("Program finished successfully.")
    except FileNotFoundError:
        logger.error(f"Error: input file not found: {input_file}")
    except ValueError as error:
        logger.error(f"Validation error: {error}")
    except Exception as error:
        logger.error(f"Unexpected error: {error}")


# Only run this code if this file is executed directly, NOT when imported
# main.py is acting like Entry point
if __name__ == "__main__":
    main()
