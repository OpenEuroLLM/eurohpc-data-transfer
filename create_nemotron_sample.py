import random
import polars as pl
from pathlib import Path

already_sampled_ids = [
    "/leonardo_work/AIFAC_L01_028/datasets/Nemotron-translated/MT-CC/MT-CC/data/parallel/eng_Latn",
    "/leonardo_work/AIFAC_L01_028/datasets/Nemotron-translated/MT-CC/MT-CC/data/additional/eng_Latn",
]

already_sampled_ids = pl.scan_parquet(already_sampled_ids).select("warc_record_id")
already_sampled_ids.sink_parquet("already_sampled_ids.parquet")


seed = random.randrange(2**64)
rows_to_sample = 160_000_000
nemotron_cc_parquet_dir = "/leonardo_work/AIFAC_L01_028/datasets/Nemotron/contrib/Nemotron/Nemotron-CC/data-parquet/quality=high/kind=actual/kind2=actual"
output_dir = "/leonardo_work/AIFAC_L01_028/datasets/Nemotron-CC-multisynt-sample2"
Path(output_dir).mkdir(exist_ok=True, parents=True)
df = pl.scan_parquet(nemotron_cc_parquet_dir)

already_sampled_ids = pl.scan_parquet("already_sampled_ids.parquet")
already_sampled_count = already_sampled_ids.select(pl.len()).collect().item()
total_rows = df.select(pl.len()).collect().item()
remaining_rows = total_rows - already_sampled_count
fraction = min(1.0, rows_to_sample / remaining_rows)

print(f"Already sampled IDs: {already_sampled_count:,}")
print(f"Total rows: {total_rows:,}")
print(f"Remaining rows: {remaining_rows:,}")
print(f"Fraction: {fraction:.4f}")

# hash-based sampling with per-run seed
df = df.join(already_sampled_ids, on="warc_record_id", how="anti")
df = df.filter(pl.col("warc_record_id").hash(seed=seed) % 10000 < round(fraction * 10000))
df.sink_parquet(
    pl.PartitionBy(output_dir, max_rows_per_file=5_000_000)
)





