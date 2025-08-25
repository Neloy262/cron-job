import click
from crontab import CronTab

# Base URL for the API endpoints
BASE_URL = "http://192.168.9.112:8020"

# Valid job names
VALID_JOBS = ["fault"]

def validate_job_name(ctx, param, value):
    """Validate that the job name is one of the valid options."""
    if value not in VALID_JOBS:
        raise click.BadParameter(f"Job name must be one of: {', '.join(VALID_JOBS)}")
    return value

@click.group()
def cli():
    """CLI tool for managing cron jobs."""
    pass

@cli.command()
@click.argument('job_name', callback=validate_job_name)
@click.argument('schedule')
def add(job_name, schedule):
    """Add a new cron job for the specified job name with the given schedule.
    
    JOB_NAME: Name of the job (fault)
    SCHEDULE: Cron schedule expression (e.g. "0 * * * *" for hourly)
    """
    cron = CronTab(user=True)
    
    # Create the command to execute
    command = f"curl -X GET {BASE_URL}/{job_name}/export/csv"
    
    # Check if job already exists
    existing_jobs = list(cron.find_command(command))
    if existing_jobs:
        click.echo(f"Job for {job_name} already exists with schedule: {existing_jobs[0].schedule()}")
        return
    
    # Create new job
    job = cron.new(command=command, comment=f"Cron job for {job_name}")
    result = job.setall(schedule)
    if result is not False:  # setall returns None on success, False on failure
        cron.write()
        click.echo(f"Successfully added cron job for {job_name} with schedule: {schedule}")
    else:
        click.echo("Invalid schedule format")

@cli.command()
@click.argument('job_name', callback=validate_job_name)
@click.argument('new_schedule')
def update(job_name, new_schedule):
    """Update an existing cron job with a new schedule.
    
    JOB_NAME: Name of the job (fault)
    NEW_SCHEDULE: New cron schedule expression
    """
    cron = CronTab(user=True)
    
    # Find the job
    command = f"curl -X GET {BASE_URL}/{job_name}/export/csv"
    jobs = list(cron.find_command(command))
    
    if not jobs:
        click.echo(f"No existing job found for {job_name}")
        return
    
    # Update the schedule
    job = jobs[0]
    result = job.setall(new_schedule)
    if result is not False:  # setall returns None on success, False on failure
        cron.write()
        click.echo(f"Successfully updated cron job for {job_name} with new schedule: {new_schedule}")
    else:
        click.echo("Invalid schedule format")

@cli.command()
@click.argument('job_name', callback=validate_job_name)
def delete(job_name):
    """Delete a cron job.
    
    JOB_NAME: Name of the job (fault)
    """
    cron = CronTab(user=True)
    
    # Find the job
    command = f"curl -X GET {BASE_URL}/{job_name}/export/csv"
    jobs = list(cron.find_command(command))
    
    if not jobs:
        click.echo(f"No existing job found for {job_name}")
        return
    
    # Remove the job
    cron.remove(jobs[0])
    cron.write()
    click.echo(f"Successfully deleted cron job for {job_name}")

@cli.command()
def list_jobs():
    """List all cron jobs managed by this tool."""
    cron = CronTab(user=True)
    
    # Find all jobs with our base URL
    found_jobs = False
    for job in cron:
        if BASE_URL in str(job.command):
            # Extract job name from command
            for job_name in VALID_JOBS:
                if f"{BASE_URL}/{job_name}/export/csv" in str(job.command):
                    # Get the schedule as a string
                    schedule_str = ' '.join([str(x) for x in job[0:5]])
                    click.echo(f"Job: {job_name} | Schedule: {schedule_str} | Command: {job.command}")
                    found_jobs = True
                    break
    
    if not found_jobs:
        click.echo("No managed cron jobs found")

if __name__ == '__main__':
    cli()
