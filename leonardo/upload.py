import os
from pathlib import Path

# Configuration - modify these as needed
source_dir = "/leonardo_work/AIFAC_L01_028/datasets/finepdfs-synt/data/eng_Latn/train-984-shards"  # absolute path on Leonardo
remote_host = "transfer3.bsc.es"  # remote SFTP host
remote_user = "ella189763"  # your username on the remote host
remote_dest = "/gpfs/scratch/ehpc532/datasets/finepdfs/data/eng_Latn/train-984-shards"  # destination path on remote host

ssh_username = os.getenv("USER")  # automatically get current username

# SSH agent forwarding for key-based auth with passphrase-protected keys.
# Before running, add your key to ssh-agent on the login node:
#   eval $(ssh-agent)
#   ssh-add ~/.ssh/id_ed25519  # enter passphrase once
# Then the -A flag forwards the agent socket to the datamover.

# Verify source exists
if not Path(source_dir).exists():
    print(f"Warning: Source directory {source_dir} does not exist locally.")
    print("Make sure the path is correct - it will be accessed from the datamover.")

# Construct the rclone command
# Using on-the-fly SFTP remote configuration (no config file needed)
# Uses ssh-agent for key-based authentication
rclone_args = [
    "rclone", "copy",
    "-vv",  # verbose output for debugging
    source_dir,
    f":sftp,host={remote_host},user={remote_user}:{remote_dest}",
    "--sftp-key-use-agent",  # use forwarded ssh-agent for authentication
    "--sftp-concurrency", "16",  # outstanding requests per connection (default 64, but 16-32 often faster)
    "--sftp-disable-hashcheck",  # skip md5 verification after transfer
    "--sftp-set-modtime=false",  # skip setting modtime on remote
    "--progress",
    "--transfers", "32",  # parallel file transfers
    "--checkers", "32",
    "--buffer-size", "256M",
    "--retries", "15",
    "--retries-sleep", "5s",
    "--low-level-retries", "15",
    "--size-only",  # compare by size only (faster than checksum)
    "--timeout", "600s",  # longer timeout for large files
    "--contimeout", "60s",  # connection timeout
    "--use-mmap",  # memory mapping for better I/O performance
    "--no-update-modtime",  # don't update modification time (faster)
]

# SSH command for datamover with agent forwarding (-A).
# Only allow hostbased authentication to the datamover itself.
ssh_command = [
    "ssh", "-Axt",  # -A forwards ssh-agent to datamover
    "-o", "PreferredAuthentications=hostbased",
    "-o", "PasswordAuthentication=no",
    "-o", "PubkeyAuthentication=no",
    "-o", "GSSAPIAuthentication=no",
    f"{ssh_username}@data.leonardo.cineca.it",
    f"""'{" ".join(f'"{arg}"' if " " in arg else arg for arg in rclone_args)}'"""
]

print("Command to execute:")
print(" ".join(ssh_command))
print()
