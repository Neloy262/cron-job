# Cron Job Manager

A CLI application to manage cron jobs with database persistence.

## Features

- Add, update, and delete cron jobs for 4 different job types (fault, pmf, imf, cmf)
- Automatically records all operations in a database
- List all managed cron jobs
- Support for predefined schedule strings (hourly, daily, weekly, monthly, yearly)

## Prerequisites

- Python 3.12+
- Poetry for dependency management
- SQL Server database

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   poetry install
   ```

## Configuration

Create a `.env` file with your database credentials and job URLs:
```
DB_HOST='your_db_host'
DB_PORT="your_db_port"
DB_NAME="your_db_name"
DB_USER="your_db_user"
DB_PASSWORD="your_db_password"

FAULT_URL="http://your_fault_service:port/fault/export/csv"
PMF_URL="http://your_pmf_service:port/pmf_report"
IMF_URL="http://your_imf_service:port/imf_report"
CMF_URL="http://your_cmf_service:port/cmf_report"
```

## Usage

```bash
# Add a new cron job with a cron expression
python cron_manager.py add fault "0 * * * *"
python cron_manager.py add pmf "0 * * * *"
python cron_manager.py add imf "0 * * * *"
python cron_manager.py add cmf "0 * * * *"

# Add a new cron job with a predefined schedule
python cron_manager.py add fault hourly
python cron_manager.py add pmf daily
python cron_manager.py add imf weekly
python cron_manager.py add cmf monthly

# Update an existing cron job with a cron expression
python cron_manager.py update <job_id> "0 0 * * *"

# Update an existing cron job with a predefined schedule
python cron_manager.py update <job_id> daily

# Delete a cron job
python cron_manager.py delete <job_id>

# List all managed cron jobs
python cron_manager.py list-jobs
```

## Valid Job Types

The application supports 4 types of jobs:
1. `fault` - Fault reporting jobs
2. `pmf` - PMF reporting jobs
3. `imf` - IMF reporting jobs
4. `cmf` - CMF reporting jobs

Each job type uses a different URL as defined in the `.env` file.

## Predefined Schedules

The following predefined schedule strings can be used instead of cron expressions:
- `hourly` - Run once an hour at minute 0
- `daily` - Run once a day at midnight
- `weekly` - Run once a week on Sunday at midnight
- `monthly` - Run once a month on the 1st at midnight
- `yearly` - Run once a year on January 1st at midnight
- `every_5_minutes` - Run every 5 minutes

## Job Management

Each cron job is automatically assigned a unique identifier when created. To update or delete specific jobs, use the `list-jobs` command to view the job IDs, then use those IDs with the update and delete commands.

For example:
1. `python cron_manager.py list-jobs` - View all jobs with their IDs
2. `python cron_manager.py update 206fc6d6 weekly` - Update the job with ID '206fc6d6' to run weekly
3. `python cron_manager.py delete 206fc6d6` - Delete the job with ID '206fc6d6'

## Database Schema

The application uses the following table structure:

```sql
CREATE TABLE [dbo].[CronJobs] (
    [Id]       INT           IDENTITY (1, 1) NOT NULL,
    [JobType]  VARCHAR (100) NOT NULL,
    [JobId]    VARCHAR (100) NULL,
    [Schedule] VARCHAR (100) NOT NULL,
    [Status]   BIT           DEFAULT ((1)) NOT NULL,
    PRIMARY KEY CLUSTERED ([Id] ASC)
);
```

When a job is deleted, its `Status` is set to 0 (false) rather than removing the record from the database.

## Technologies Used

- Python
- Click for CLI interface
- python-crontab for cron job management
- SQLAlchemy for ORM
- python-decouple for environment variable management
- pyodbc for SQL Server connection