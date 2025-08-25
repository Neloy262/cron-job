# Cron Job Manager

A CLI tool for managing cron jobs that call REST API endpoints.

## Features

- Add cron jobs
- Update cron jobs
- Delete cron jobs
- List all managed cron jobs

## Installation

```bash
poetry install
```

## Usage

```bash
# Add a new cron job
python cron_manager.py add fault "0 * * * *"

# Update an existing cron job
python cron_manager.py update fault "0 0 * * *"

# Delete a cron job
python cron_manager.py delete fault

# List all cron jobs
python cron_manager.py list_jobs
```

## Job Types

1. `fault` - Fault monitoring endpoint

All jobs call the corresponding endpoint at `http://192.168.9.112/{job_name}/export/csv`

## Schedule Format

The schedule follows the standard cron format:
```
* * * * * *
| | | | | |
| | | | | +-- Day of Week (0-6 or Sun-Sat)
| | | | +---- Month (1-12 or Jan-Dec)
| | | +------ Day of Month (1-31)
| | +-------- Hour (0-23)
| +---------- Minute (0-59)
+------------ Second (0-59, optional)
```

Examples:
- `0 * * * *` - Every hour
- `0 0 * * *` - Every day at midnight
- `0 0 * * 0` - Every Sunday at midnight