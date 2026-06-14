# Backup and Restore Runbook

The company runs nightly backups of the file server and all databases. Backups
are the last line of defense against ransomware and accidental deletion, so
verifying them matters as much as taking them.

## Schedule

Full backups run every Sunday at 01:00. Incremental backups run nightly at 01:00
on the other six days. Backups are written to the on-site backup appliance and
replicated off-site to cloud storage within four hours.

## Verifying backups

A backup you cannot restore is not a backup. Once a month, perform a test
restore of a sample file and a sample database to the staging environment and
confirm the data opens correctly. Record the test result in the ticketing
system. A failed verification is a priority incident.

## Restoring data

To restore a deleted file, open the backup console, browse to the date before
the deletion, and restore to the original path or to staging. For a full
database restore, coordinate with the application owner and restore to staging
first, never directly over production. Always confirm the restore point with the
requester before overwriting any live data.
