# Protected holdout

Operator-invoked only. Candidate code and optimizers must not read or write this directory
(protected by src/agent_os/orchestrator/control_plane.py). Store real private holdout cases
machine-locally and keep only a manifest (case count, checksum, refresh date) here.
No cases yet.
