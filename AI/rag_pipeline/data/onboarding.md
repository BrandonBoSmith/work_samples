# New Employee Onboarding

This runbook covers provisioning a new employee on their first day. The goal is
for the new hire to have a working laptop, email, and access to the systems
their role requires before lunch.

## Accounts

Create the user in the identity provider, which automatically provisions email
and a network password. Have the new hire set their password and register an
authenticator app for multi-factor authentication immediately. Add the user to
the security groups that match their department.

## Equipment

Issue a laptop from the imaged-device pool and record the asset tag against the
employee. Install the VPN client and confirm the new hire can connect from the
office network. Walk them through connecting so they can do it themselves when
working remotely.

## Access

Grant access to the ticketing system, the shared file server, and any
department-specific applications. Follow least privilege: grant only what the
role needs. Access requests beyond the standard role template require manager
approval recorded in a ticket.
