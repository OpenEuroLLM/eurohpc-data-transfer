from pathlib import Path
import duckdb
from tqdm.auto import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKERS = 4

d = Path("/leonardo_work/AIFAC_L01_028/datasets/HPLT3/deu_Latn")

files = list(d.glob("**/*.jsonl.zst"))
output_files = [Path(str(f).replace(".jsonl.zst", ".zstd.parquet").replace("HPLT3", "HPLT3-parquet")) for f in files]

print(f"d: {d}")
print(f"files: {len(files)}")
print(f"output directory: {output_files[0].parent}")

KEEP_COLUMNS = ["id", "text"]

def convert_file(file_pair):
    """Convert a single JSONL file to Parquet format using DuckDB"""
    file, output_file = file_pair
    try:
        if output_file.exists():
            return f"Skipping {file.name} because output file {output_file} it already exists"
        
        output_file.parent.mkdir(exist_ok=True, parents=True)
        tmp_file = output_file.with_suffix(".tmp")
        
        # Use a fresh connection per thread with streaming settings
        con = duckdb.connect()
        con.execute("SET memory_limit = '470GB'")
        con.execute("SET preserve_insertion_order = false")  # Enable parallel/streaming
        con.execute("SET temp_directory = '/leonardo_scratch/large/userexternal/midahl00/duckdb_temp'")  # Allow spilling to disk
        
        columns = ", ".join(KEEP_COLUMNS)
        con.execute(f"""
            COPY (
                SELECT {columns}
                FROM read_json(
                    '{file}',
                    format = 'newline_delimited',
                    columns = {{id: 'VARCHAR', text: 'VARCHAR'}}
                )
            )
            TO '{tmp_file}' (FORMAT PARQUET, COMPRESSION ZSTD)
        """)
        con.close()
        
        tmp_file.rename(output_file)
        return f"Successfully converted {file.name}"
    except Exception as e:
        import traceback
        return f"Error converting {file.name}: {str(e)}\n{traceback.format_exc()}"

print(f"Processing {len(files)} files using {WORKERS} workers...")

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    file_pairs = list(zip(files, output_files))
    future_to_file = {executor.submit(convert_file, file_pair): file_pair for file_pair in file_pairs}
    
    with tqdm(total=len(files), desc="Converting files") as pbar:
        for future in as_completed(future_to_file):
            result = future.result()
            pbar.write(result)
            pbar.update(1)
