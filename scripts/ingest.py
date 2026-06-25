import os
import time
import logging

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///inventory.db")

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
)

CHUNK_SIZE = 100_000


def ingest_csv(file_path, table_name):
    start = time.time()

    first_chunk = True
    chunk_no = 1

    for chunk in pd.read_csv(
        file_path,
        chunksize=CHUNK_SIZE,
        low_memory=False,
    ):
        chunk.to_sql(
            table_name,
            con=engine,
            if_exists="replace" if first_chunk else "append",
            index=False,
        )

        print(
            f"✓ {table_name} | "
            f"Chunk {chunk_no} | "
            f"{len(chunk):,} rows"
        )

        logging.info(
            f"{table_name}: "
            f"Chunk {chunk_no} inserted "
            f"({len(chunk):,} rows)"
        )

        first_chunk = False
        chunk_no += 1

    elapsed = time.time() - start

    print(
        f"✓ {table_name} completed "
        f"in {elapsed:.2f}s"
    )

    logging.info(
        f"{table_name} completed "
        f"in {elapsed:.2f}s"
    )


def load_raw_data():
    start = time.time()

    logging.info(
        "------------- Ingestion Started -------------"
    )

    for file in os.listdir("data"):

        if not file.endswith(".csv"):
            continue

        file_path = os.path.join("data", file)
        table_name = os.path.splitext(file)[0]

        try:
            logging.info(f"Starting {file}")
            print(f"\nStarting {file}")

            ingest_csv(file_path, table_name)

        except Exception:
            logging.exception(
                f"Error processing {file}"
            )

            print(
                f"\n✗ Error processing {file}"
            )

    total = (time.time() - start) / 60

    logging.info(
        "------------- Ingestion Complete -------------"
    )

    logging.info(
        f"Total Time Taken: {total:.2f} minutes"
    )

    print(
        "\n------------- Ingestion Complete -------------"
    )

    print(
        f"Total Time Taken: {total:.2f} minutes"
    )


if __name__ == "__main__":
    load_raw_data()