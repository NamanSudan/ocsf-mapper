# Windows Event to OCSF Mapping

This document describes how Windows Security Events are mapped to the OCSF schema.

## Event Class Mappings

| Windows Event ID | OCSF Class | Description |
|-----------------|------------|-------------|
| 4624 | Authentication (1001) | Successful logon |
| 4625 | Authentication (1001) | Failed logon |
| 4688 | Process Activity (1002) | Process creation |

## Field Mappings

### Authentication Events
- SubjectUserName → actor.user.name
- TargetUserName → target.user.name
- WorkstationName → device.hostname
- IpAddress → device.ip

### Process Events
- ProcessName → process.name
- CommandLine → process.cmd_line
- ParentProcessId → process.parent_process.pid

## Criticality Levels
Events are classified into three criticality levels:
- High: Requires immediate attention
- Medium: Requires monitoring
- Low: Informational

## Metrics
The following metrics are collected:
- Total events mapped
- Mapping errors by type
- High criticality events
- Schema validation failures 