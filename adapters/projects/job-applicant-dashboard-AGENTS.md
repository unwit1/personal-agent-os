# Job Applicant Dashboard agent entry point

Route development through project `job-applicant-dashboard` in the Personal
Agent OS. Use synthetic data only. Never read, index, commit, or transmit live
applicant spreadsheets, PDFs, resumes, database rows, caches, drafts, sent
email, backups, credentials, or local configuration. Never send applicant
communications automatically. `README.md` is the current runtime guide;
`CLAUDE.md` contains detailed implementation guidance when a task requires it.


For work involving Fillout, applicant intake, Agent OS, connectors, or
cross-surface automation, read `docs/AGENT_OS_INTEGRATION.md` before changing
the data path. The canonical direction is Fillout -> Google bridge ->
`process_applications.py` -> Applicant Dashboard -> Agent OS. Do not create a
second raw-Fillout applicant pipeline, expose EEO/self-ID data to hiring tools,
or commit live applicant data/credentials.

Agent OS integration must remain administrative/supportive: it may organize, summarize, track missing documents, schedule, and prepare user-directed drafts, but it must not rank applicants, recommend employment outcomes, or use restricted self-identification data in employment decisions.
