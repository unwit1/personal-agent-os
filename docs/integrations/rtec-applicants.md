# RTEC Applicant Connector

Status: planned / implementation-ready  
Privacy domain: restricted work HR

The RTEC applicant connector exposes the normalized local Applicant Dashboard
to Agent OS. Fillout remains upstream and currently reaches the Dashboard via
Google Sheets/Drive.

See:

- `projects/personal-agent-os/roadmap/rtec-applicant-pipeline.md`
- `knowledge/libraries/rtec-hr/systems/fillout-applicant-dashboard-agent-os-integration.json`
- `unwit1/job-applicant-dashboard/docs/AGENT_OS_INTEGRATION.md` (external canonical application repo)

Key rule: Agent OS connects to the Dashboard normalization/workflow layer, not
to an independent raw-Fillout applicant store.

Do not register this connector as healthy/registered until the local adapter and
privacy tests are implemented and pass.
