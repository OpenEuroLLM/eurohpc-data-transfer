import os
from pathlib import Path
from huggingface_hub import list_repo_files, get_token


repo_id = "nvidia/Nemotron-CC-v2.1"
repo_type = "dataset"
revision = "main"
output_dir = "/leonardo_work/AIFAC_L01_028/datasets/Nemotron-CC-v2.1" # put your output directory here
ssh_username = os.getenv("USER") # automatically get current username

# Ensure output directory exists
Path(output_dir).mkdir(parents=True, exist_ok=True)
print(f"Output directory: {output_dir}")

hf_token = get_token()
if hf_token:
    print("Using HuggingFace token")
else:
    print("No HuggingFace token found")

# Get list of all files in the repository
files = list_repo_files(repo_id=repo_id, repo_type=repo_type, revision=revision, token=hf_token)

# Save files list to file_list.txt
list_file_path = Path(output_dir) / "file_list.txt" 
with open(list_file_path, "w") as f:
    f.write("\n".join(files))

print(f"Saved {len(files)} files to {list_file_path}")

# Dynamically construct the HTTP URL
if repo_type == "dataset":
    http_url = f"https://huggingface.co/datasets/{repo_id}/resolve/{revision}/"
else:
    http_url = f"https://huggingface.co/{repo_id}/resolve/{revision}/"

print(f"HTTP URL: {http_url}")

# Construct the rclone command
rclone_base_args = [
    "rclone", "copy",
    "-vv",
    "--files-from", str(list_file_path.absolute()),
    "--no-traverse",
    "--transfers", "16",
    "--checkers", "16",
    "--progress",
    "--retries", "15",
    "--retries-sleep", "5s",
    "--low-level-retries", "15",
    "--size-only",
    "--http-no-head",
    "--multi-thread-streams", "3",
    "--multi-thread-cutoff", "200M",
    "--buffer-size", "128M",
    "--tpslimit", "3",
    "--timeout", "600s",
    "--contimeout", "60s",
    "--expect-continue-timeout", "10s",
    "--disable-http2",
    "--user-agent", "rclone/leonardo-hpc",
    "--no-check-certificate",
    "--use-mmap",
    "--no-update-modtime",
]

# Add authentication header if token is available
if hf_token:
    rclone_base_args.extend([
        "--header", f"Authorization: Bearer {hf_token}"
    ])

# Add HTTP URL and destination
rclone_base_args.extend([
    "--http-url", http_url,
    ":http:",
    output_dir
])

# SSH command for datamover. Only allow hostbased authentication.
ssh_command = [
    "ssh", "-xt", 
    "-o", "PreferredAuthentications=hostbased",
    "-o", "PasswordAuthentication=no",
    "-o", "PubkeyAuthentication=no",
    "-o", "GSSAPIAuthentication=no",
    f"{ssh_username}@data.leonardo.cineca.it",
    f"""'{" ".join(f'"{arg}"' if " " in arg else arg for arg in rclone_base_args)}'"""
]

print("Command to execute:")
print(" ".join(ssh_command))
print()

# Example output when running the command:
# 2025/07/09 15:02:33 NOTICE: Config file "/home/.rclone.conf" not found - using defaults
# 2025/07/09 15:02:39 NOTICE: Time may be set wrong - time from "cdn-lfs-us-1.hf.co" is 306h34m3.435898448s different from this computer
# Transferred:       38.997 GiB / 38.997 GiB, 100%, 1.262 GiB/s, ETA 0s
# Checks:               350 / 350, 100%
# Transferred:           19 / 9241, 0%
# Elapsed time:        39.0s
# Transferring:
#  *         data/arb_Arab/train/000_00001.parquet:  0% /off, 198.771Mi/s, -
#  *         data/arb_Arab/train/000_00004.parquet:  0% /off, 172.021Mi/s, -
#  *         data/arb_Arab/train/001_00000.parquet:  0% /off, 211.299Mi/s, -
#  *         data/arb_Arab/train/001_00001.parquet:  0% /off, 210.342Mi/s, -
#  *         data/arb_Arab/train/001_00002.parquet:  0% /off, 213.998Mi/s, -
#  *         data/arb_Arab/train/001_00003.parquet:  0% /off, 0/s, -
#  *         data/arb_Arab/train/001_00004.parquet: transferring
#  *         data/arb_Arab/train/002_00000.parquet: transferring
