# Leonardo

Data transfer tools for Leonardo's datamover nodes using rclone.

| Direction  | Method                | Tool / Config          | Description                                              |
|------------|-----------------------|------------------------|----------------------------------------------------------|
| Download   | HTTP URL list         | rclone + file list     | Download files from any HTTP source using a file list    |
| Download   | HuggingFace           | `hf_download.py`       | Download a HuggingFace repo via the datamover node       |
| Download   | LUMI-O (S3)           | rclone + S3 credentials| Download files from LUMI-O object storage via S3         |
| Upload     | SFTP to remote cluster| `upload.py`            | Upload data from Leonardo to a remote cluster (e.g. BSC) |


## Download

### Downloading a list of HTTP urls
Create a file with a list of file paths, relative to shared http-url prefix. For example, to grab one file from swedish and finnish HPLT3 each:
```
# /leonardo_work/AIFAC_L01_028/datasets/HPLT3/file_list.txt 
fin_Latn/10_1.jsonl.zst
swe_Latn/10_1.jsonl.zst
```
Their shared http-url prefix is `https://data.hplt-project.org/three/sorted/`.

Command to download on leonardo datamover:
```
ssh -xt -o PreferredAuthentications=hostbased -o PasswordAuthentication=no -o PubkeyAuthentication=no -o GSSAPIAuthentication=no midahl00@data.leonardo.cineca.it 'rclone copy -vv --files-from /leonardo_work/AIFAC_L01_028/datasets/HPLT3/file_list.txt --no-traverse --transfers 16 --checkers 16 --progress --retries 15 --retries-sleep 5s --low-level-retries 15 --size-only --http-no-head --multi-thread-streams 3 --multi-thread-cutoff 200M --buffer-size 128M --tpslimit 3 --timeout 600s --contimeout 60s --expect-continue-timeout 10s --disable-http2 --user-agent rclone/leonardo-hpc --no-check-certificate --use-mmap --no-update-modtime --http-url https://data.hplt-project.org/three/sorted/ :http: /leonardo_work/AIFAC_L01_028/datasets/HPLT3'
```
This will populate `/leonardo_work/AIFAC_L01_028/datasets/HPLT3`:
```
file_list.txt
fin_Latn/
swe_Latn/
```


### Downloading from HuggingFace

`hf_download.py` creates a command for downloading a HuggingFace repo via the datamover node.

```bash
python hf_download.py
# Prints an ssh command to run on a Leonardo login node
```

#### Example output

```bash
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
```

The progress indicator is a bit screwed because we do not want to send a head request to hf for every file, so rclone does not know the file sizes and cannot give you an estimate.

### Downloading from LUMI

Example to download files from LUMI-O via datamover:
```bash
export LUMIO_ACCESS_KEY=EQ4...
export LUMIO_SECRET_KEY=xj2...
ssh -xt -o PreferredAuthentications=hostbased -o PasswordAuthentication=no -o PubkeyAuthentication=no -o GSSAPIAuthentication=no midahl00@data.leonardo.cineca.it "rclone copy -vv --transfers 16 --checkers 16 --progress --retries 15 --retries-sleep 5s --low-level-retries 15 --size-only --multi-thread-streams 3 --multi-thread-cutoff 200M --buffer-size 128M --timeout 600s --contimeout 60s --no-update-modtime --use-mmap --s3-provider Other --s3-endpoint https://lumidata.eu --s3-env-auth=false --s3-access-key-id ${LUMIO_ACCESS_KEY} --s3-secret-access-key ${LUMIO_SECRET_KEY} --s3-no-check-bucket :s3:462000963:hplt4 /leonardo_work/AIFAC_L01_028/datasets/hplt4"
```


## Upload

### Upload to remote cluster via SFTP

`upload.py` creates a command for uploading data from Leonardo to a remote cluster (e.g., BSC) via SFTP.

#### Setup

1. Ensure you have SSH key-based authentication set up with the remote cluster
2. Edit `upload.py` to configure:
   - `source_dir` - absolute path on Leonardo
   - `remote_host` - remote SFTP hostname
   - `remote_user` - your username on the remote host
   - `remote_dest` - destination path on the remote host

#### Usage

```bash
# 1. Add your SSH key to ssh-agent (handles passphrase-protected keys)
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519

# 2. Generate the command
python upload.py

# 3. Run the printed ssh command
```

Uses SSH agent forwarding (`-A`) to authenticate with the remote cluster from the datamover.

### Example output

```
Transferred:      162.052 GiB / 3.006 TiB, 5%, 446.079 MiB/s, ETA 1h51m34s
Checks:                 1 / 1, 100%
Transferred:            1 / 144, 1%
Elapsed time:      6m33.9s
Transferring:
 *                        spa_Latn/5_1.jsonl.zst: 22% /22.803Gi, 13.725Mi/s, 22m0s
 *                        spa_Latn/5_2.jsonl.zst: 22% /22.584Gi, 14.185Mi/s, 21m2s
 *                        spa_Latn/5_3.jsonl.zst: 22% /22.357Gi, 14.174Mi/s, 20m52s
 *                        spa_Latn/5_4.jsonl.zst: 21% /22.179Gi, 13.173Mi/s, 22m35s
 *                        spa_Latn/6_1.jsonl.zst: 22% /23.480Gi, 14.151Mi/s, 22m1s
 ...
```

#### Notes

- The datamover is containerized, so you'll see harmless errors about config files
- If the transfer is interrupted, rerun the same command - rclone resumes automatically
- Uses `--size-only` for fast comparison on resume