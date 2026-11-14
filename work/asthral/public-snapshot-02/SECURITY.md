# ASTHRAL security boundaries

Research prototype, synthetic data only. Reader credentials are scoped by astronaut and mission; the portal holds no clinical write credential. Trusted local configuration controls optional public retrieval. There is no online-enable/medical-authorization endpoint for a reader or model. Remote metadata is untrusted, never executed, and never supplied to the LLM or clinical rule engine.

Never commit .env files, credentials, DPAPI envelopes, databases, backups, runtime logs/configuration, models, or private mission data. If a credential is exposed, stop publication and follow the owner's revocation/remediation process; removing a file from the working tree does not remove history. Report a suspected issue privately to the repository owner; do not publish private clinical records in an issue.

TLS verification remains enabled. The public provider uses approved fixed paths, no proxies/cookies/private headers, rejected redirects, validated public addresses pinned for connection, bounded JSON, and fixed public topics. No arbitrary URL or private question is accepted by the retrieval component. These controls do not protect against a fully compromised OS or same-user process.

SQLite, WAL and backups lack encryption. Audit/hash checks detect internal inconsistency within the design but are not an external trust anchor against storage/codespace control. Process isolation, operational identity governance, verified clinical authority, encryption and independent review remain pending. A private GitHub repository does not make unsafe content safe to upload. No treatment execution is enabled.
