# Security Incident Response

A security incident is any event that may compromise the confidentiality,
integrity, or availability of company systems or data -- malware, a phishing
click, a lost laptop, or suspected account compromise. Speed and clear
communication matter more than assigning blame.

## Report immediately

Anyone who suspects an incident must report it right away by opening a priority
ticket and messaging the security channel. Do not try to fix it quietly. If an
account may be compromised, the first containment step is to disable that
account in the identity provider, which cuts off email and VPN access at once.

## Contain and assess

Isolate affected devices from the network -- disconnect the VPN and unplug
ethernet, but do not power the machine off, as that can destroy forensic
evidence. Assess scope: which accounts, which data, and whether backups are
intact. Reset the passwords of any potentially compromised accounts and require
re-registration of multi-factor authentication.

## Recover and review

Restore affected systems from a known-good backup once the threat is removed.
After recovery, hold a blameless review within five business days to capture
what happened, what worked, and what to change. Record the findings and any
follow-up actions in the ticketing system.
