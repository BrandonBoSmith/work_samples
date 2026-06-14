# Employee Offboarding

When an employee leaves, their access must be revoked promptly to protect
company data. This runbook should be completed on the employee's last day,
ideally within an hour of their departure being confirmed by HR.

## Disable access

Disable the user account in the identity provider first. This single action
revokes email, VPN, and ticketing-system access at once because they all
authenticate against the same directory. Do not delete the account yet -- it is
needed to transfer ownership of files and mailboxes.

## Recover equipment

Collect the employee's laptop and any peripherals, and mark the asset tag as
returned. Wipe the device and return it to the imaged-device pool. If the laptop
cannot be recovered (for example a fully remote worker), remotely wipe it and
flag the asset as pending return.

## Transfer and archive

Transfer ownership of the departing employee's files and shared documents to
their manager. Set an out-of-office auto-reply on their mailbox and forward
incoming mail to the manager for 30 days. After 30 days, archive the mailbox and
delete the account.
