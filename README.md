# Harbor Registry Cleaner

This Python script automates the process of deleting unnecessary artifacts (docker images) from a Harbor registry. It is designed to be used as an internal tool within a company, and is primarily run via a Jenkins job.

## Requirements

- Python 3.6.15 or higher
- requirements.txt

## Usage

The script can be run with the following command:

```bash
python3 harbor-clean.py --project PROJECT_NAME --days 120 --count 4 --user USERNAME --password PASSWORD
````

Get help/instructions:
```bash
python3 harbor-clean.py --help
```

By default, this command performs a dry run, meaning it will only log the artifacts that would be deleted without actually deleting them.

To perform a deletion run that will permanently delete artifacts, use the `--deletionRun` flag:

```bash
python3 harbor-clean.py --project PROJECT_NAME --days 120 --count 4 --user USERNAME --password PASSWORD --deletionRun
```

## Parameters

- `--project PROJECT_NAME`: The name of the project in the Harbor registry.
- `--days 120`: The number of days to retain artifacts. Artifacts older than this will be deleted.
- `--count 4`: The number of artifacts to retain per repository. Additional artifacts will be deleted.
- `--user USERNAME`: The username for the Harbor registry.
- `--password PASSWORD`: The password for the Harbor registry.
-   `--url HARBOR_URL`: URL pointing to your Harbor
- `--deletionRun`: This flag indicates that the script should delete artifacts. Without this flag, the script will only perform a dry run.

## Disclaimer

Please use this script with caution. Deleting artifacts is a permanent action and cannot be undone.
Please replace `PROJECT_NAME`, `USERNAME`, and `PASSWORD` with your actual project name, username, and password respectively when running the script.
