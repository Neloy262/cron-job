import click
import uuid
from crontab import CronTab
from database import create_cron_job, update_cron_job, delete_cron_job
from decouple import Config, RepositoryEnv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
config = Config(RepositoryEnv(env_path))

# Base URLs for the API endpoints
JOB_URLS = {
    "fault": config('FAULT_URL'),
    "pmf": config('PMF_URL'),
    "imf": config('IMF_URL'),
    "cmf": config('CMF_URL')
}

# Valid job names
VALID_JOBS = ["fault", "pmf", "imf", "cmf"]

# Schedule string mappings to cron expressions
SCHEDULE_MAPPINGS = {
    "yearly": "0 0 1 1 *",      # January 1st at midnight
    "monthly": "0 0 1 * *",     # 1st of every month at midnight
    "weekly": "0 0 * * 0",      # Every Sunday at midnight
    "daily": "0 0 * * *",       # Every day at midnight
    "hourly": "0 * * * *",      # Every hour at minute 0
    "every_5_minutes": "*/5 * * * *",  # Every 5 minutes
}

# Reverse mapping for checking if a cron expression is a predefined schedule
REVERSE_SCHEDULE_MAPPINGS = {v: k for k, v in SCHEDULE_MAPPINGS.items()}

def validate_job_name(ctx, param, value):
    """Validate that the job name is one of the valid options."""
    if value not in VALID_JOBS:
        raise click.BadParameter(f"Job name must be one of: {', '.join(VALID_JOBS)}")
    return value

def parse_schedule(schedule):
    """Convert schedule string to cron expression if it's a predefined schedule."""
    return SCHEDULE_MAPPINGS.get(schedule.lower(), schedule)

def is_predefined_schedule(schedule):
    """Check if a schedule is a predefined schedule string."""
    return schedule.lower() in SCHEDULE_MAPPINGS

@click.group()
def cli():
    """CLI tool for managing cron jobs."""
    pass

@cli.command()
@click.argument('job_name', callback=validate_job_name)
@click.argument('schedule')
def add(job_name, schedule):
    """Add a new cron job for the specified job name with the given schedule.
    
    JOB_NAME: Name of the job (fault, pmf, imf, cmf)
    SCHEDULE: Cron schedule expression (e.g. "0 * * * *" for hourly) or predefined schedule (hourly, daily, weekly, monthly, yearly)
    """
    # Parse schedule string to cron expression if needed
    parsed_schedule = parse_schedule(schedule)
    
    cron = CronTab(user=True)
    
    # Generate a unique identifier for this job
    job_id = str(uuid.uuid4())[:8]  # Short UUID for readability
    
    # Get the appropriate URL for this job type
    base_url = JOB_URLS[job_name]
    
    # Create the command to execute with the job ID as a query parameter or path parameter
    # We'll add the job ID as a query parameter to avoid changing the URL structure
    if "?" in base_url:
        command = f"curl -X GET \"{base_url}&jobId={job_id}\""
    else:
        command = f"curl -X GET \"{base_url}?jobId={job_id}\""
    
    comment = f"Cron job for {job_name} (ID: {job_id})"
    
    # Create new job
    job = cron.new(command=command, comment=comment)
    result = job.setall(parsed_schedule)
    if result is not False:  # setall returns None on success, False on failure
        cron.write()
        # Record in database - store the original schedule string, not the parsed one
        try:
            db_job = create_cron_job(job_name, schedule, job_id)
            click.echo(f"Successfully added cron job for {job_name} with ID '{job_id}' and schedule: {schedule}")
        except Exception as e:
            click.echo(f"Failed to record job in database: {str(e)}")
            # Rollback cron job if database recording fails
            cron.remove(job)
            cron.write()
            return
    else:
        click.echo("Invalid schedule format")
        return

@cli.command()
@click.argument('job_id')
@click.argument('new_schedule')
def update(job_id, new_schedule):
    """Update an existing cron job with a new schedule.
    
    JOB_ID: The unique identifier of the job to update
    NEW_SCHEDULE: New cron schedule expression or predefined schedule (hourly, daily, weekly, monthly, yearly)
    """
    # Parse schedule string to cron expression if needed
    parsed_schedule = parse_schedule(new_schedule)
    
    cron = CronTab(user=True)
    
    # Find the job by ID
    found_job = None
    for job in cron:
        if f"jobId={job_id}" in str(job.command):
            found_job = job
            break
    
    if not found_job:
        click.echo(f"No existing job found with ID '{job_id}'")
        return
    
    # Save the original schedule for potential rollback
    original_schedule = found_job.schedule()
    
    # Update the schedule
    result = found_job.setall(parsed_schedule)
    if result is not False:  # setall returns None on success, False on failure
        cron.write()
        # Update in database - store the original schedule string, not the parsed one
        try:
            # We need to extract the job type from the command
            command = str(found_job.command)
            job_type = None
            for jt in VALID_JOBS:
                base_url = JOB_URLS[jt]
                if base_url in command and f"jobId={job_id}" in command:
                    job_type = jt
                    break
            
            if job_type:
                updated_job = update_cron_job(job_type, new_schedule, job_id)
                if updated_job:
                    click.echo(f"Successfully updated cron job with ID '{job_id}' and new schedule: {new_schedule}")
                else:
                    click.echo(f"Found cron job with ID '{job_id}' but failed to update in database")
                    # Rollback the cron job if database update fails
                    found_job.setall(original_schedule)
                    cron.write()
            else:
                click.echo(f"Could not determine job type for job with ID '{job_id}'")
                # Rollback the cron job
                found_job.setall(original_schedule)
                cron.write()
        except Exception as e:
            click.echo(f"Failed to update job in database: {str(e)}")
            # Rollback the cron job if database update fails
            found_job.setall(original_schedule)
            cron.write()
    else:
        click.echo("Invalid schedule format")

@cli.command()
@click.argument('job_id')
def delete(job_id):
    """Delete a cron job.
    
    JOB_ID: The unique identifier of the job to delete
    """
    cron = CronTab(user=True)
    
    # Find the job by ID
    found_job = None
    for job in cron:
        if f"jobId={job_id}" in str(job.command):
            found_job = job
            break
    
    if not found_job:
        click.echo(f"No existing job found with ID '{job_id}'")
        return
    
    # Save the job for potential rollback
    job = found_job
    
    # Mark as deleted in database first
    db_success = False
    try:
        # We need to extract the job type from the command
        command = str(job.command)
        job_type = None
        for jt in VALID_JOBS:
            base_url = JOB_URLS[jt]
            if base_url in command and f"jobId={job_id}" in command:
                job_type = jt
                break
        
        if job_type:
            db_success = delete_cron_job(job_type, job_id)
        else:
            click.echo(f"Could not determine job type for job with ID '{job_id}'")
            return
    except Exception as e:
        click.echo(f"Failed to mark job as deleted in database: {str(e)}")
        return
    
    if db_success:
        # Remove the job from cron only after successful database update
        cron.remove(job)
        cron.write()
        click.echo(f"Successfully deleted cron job with ID '{job_id}'")
    else:
        click.echo(f"Failed to delete cron job with ID '{job_id}' in database")

@cli.command()
def list_jobs():
    """List all cron jobs managed by this tool."""
    cron = CronTab(user=True)
    
    # Find all jobs with our base URLs
    found_jobs = False
    for job in cron:
        command_str = str(job.command)
        # Check if this job's command matches any of our job types
        for job_name in VALID_JOBS:
            base_url = JOB_URLS[job_name]
            if base_url in command_str:
                # Get the schedule as a string
                schedule_str = ' '.join([str(x) for x in job[0:5]])
                # Try to find if this matches a predefined schedule
                display_schedule = REVERSE_SCHEDULE_MAPPINGS.get(schedule_str, schedule_str)
                
                # Extract ID from query parameter jobId=
                if "jobId=" in command_str:
                    start_idx = command_str.find("jobId=") + 6  # Length of "jobId="
                    end_idx = command_str.find("\"", start_idx)
                    if end_idx == -1:  # If no closing quote, find end of string or next space
                        end_idx = len(command_str)
                    job_id = command_str[start_idx:end_idx]
                    click.echo(f"Job: {job_name} | ID: {job_id} | Schedule: {display_schedule} | Command: {job.command}")
                else:
                    click.echo(f"Job: {job_name} | Schedule: {display_schedule} | Command: {job.command}")
                found_jobs = True
                break
    
    if not found_jobs:
        click.echo("No managed cron jobs found")

if __name__ == '__main__':
    cli()
