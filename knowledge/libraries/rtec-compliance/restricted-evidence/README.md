# Restricted compliance evidence rules

The compliance archive contains large volumes of person-specific HR/compliance information.

## Always metadata-only

- applicant logs and applicant tracking workbooks;
- completed affirmative-action / voluntary demographic forms;
- employee EEO/demographic rosters;
- payroll/person-level EEO upload data;
- EEOC charge/case files;
- individual reasonable-accommodation case records;
- completed complaint/investigation records that identify individuals;
- any source containing SSNs, DOBs, addresses, medical/disability facts, beneficiary information, or comparable identifiers.

## Safe generalized evidence

Restricted sources may support only statements such as:
- a workflow or form existed;
- a fiscal-year log was maintained;
- a type of complaint/accommodation process was used;
- aggregate counts or non-identifying statistics were used in a plan.

A single case never establishes a global rule.

## Filename sanitization

When a restricted source filename contains a person's name, the GitHub manifest must replace it with an opaque identifier based on the source hash. The original name remains only in the user's source archive, not in the generalized repository.
