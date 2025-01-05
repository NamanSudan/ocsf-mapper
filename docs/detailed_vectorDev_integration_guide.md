```markdown:detailed_vectorDev_integration_guide.md
# Detailed Vector.dev Integration Guide

This guide explains how to integrate [Vector.dev](https://github.com/vectordotdev/vector) into our “dynamic security log mapping” solution. The instructions here build on top of our existing architecture as outlined in:  
• [Detailed Design Document](../docs/design-docs/detailed-design.md)  
• [Backend Design Document](../docs/design-docs/detailed_backend_design_doc.md)  

By combining the performance and flexibility of Vector with our ingestion, classification, and knowledge base services, we gain a scalable, observability-grade pipeline for handling security logs prior to mapping them to OCSF classes.

---

## 1. Overview & Rationale

Vector.dev is an open source “observability data pipeline” tool. It can collect logs (and metrics) from numerous sources, perform transformations, and route data to our ingestion service (or a message queue in front of it). The synergy between Vector and our solution includes:

1. Ingesting logs from multiple platforms (Windows Event Log, Syslog, containers, etc.) at scale.  
2. Applying filtering or light transformations at the edge.  
3. Forwarding structured events into our ingestion-service, which then normalizes them for classification.  
4. Ensuring reliability and observability with minimal overhead.

Refer to the “Ingestion Service” section of the [detailed_backend_design_doc.md](../docs/design-docs/detailed_backend_design_doc.md#31-ingestion-service) to see how logs flow into our pipeline. Vector acts as the first hop in that chain.

---

## 2. Prerequisites

1. A working Docker Compose environment (or Kubernetes if you plan to run Vector in a cluster).  
2. Our repository with the ingestion-service module present.  
3. A basic understanding of Vector’s configuration model (sources, transforms, sinks). The official Vector repo (https://github.com/vectordotdev/vector) provides an in-depth reference.

---

## 3. Repository Structure Integration

Below is a simplified diagram showing how Vector fits into the broader system:

```
  [Various Log Sources]
        | (HTTP, file, syslog, Windows events, etc.)
        v
     Vector.dev
        |  (over HTTP or TCP)
        v
  ingestion-service (Flask / Python)
        |
        v
 classification-service (Flask / Python)
        |
        v
   knowledge-base
        +---> Trieve or local DB
```

In many cases, Vector runs in its own container—either as a sidecar or external agent on each host. You can store its configuration in the `docker/` folder if you want to reuse the same Compose orchestration for local development.

---

## 4. Setting Up Vector Locally

### 4.1 Installing or Containerizing

• Local Installation (bare metal or VMs):  
  - Download pre-built binaries or use package managers.  
  - For more details, see Vector’s official documentation:  
    [Quickstart guide @ Vector.dev](https://github.com/vectordotdev/vector#quickstart).  

• Docker Container:  
  - Add a `vector` service to your `docker-compose.yml`.  
  - Example snippet:

```yaml:docker/docker-compose.yml
vector:
  image: timberio/vector:latest
  container_name: vector
  volumes:
    - ./docker/vector/vector.toml:/etc/vector/vector.toml:ro
  ports:
    - "9000:9000"      # for HTTP source
    - "9001:9001"      # optional for Vector's internal metrics
  restart: unless-stopped
```

*(Note: The official Docker image is typically found at docker.io/timberio/vector or vectordotdev/vector, but check the official docs for the latest details.)*

---

## 5. Vector Configuration Example

In the [detailed_backend_design_doc.md](../docs/design-docs/detailed_backend_design_doc.md#data-flow-example), we mention logs arriving from sources like syslog or Windows events. Here is a sample `vector.toml` config that demonstrates how to:

1. Collect logs from a file source  
2. Perform minimal transforms (e.g., parse JSON if needed)  
3. Output to our ingestion-service over HTTP

```toml:docker/vector/vector.toml
# vector.toml
# ------------------------------------------------------------------------------
# Example configuration for sending logs to the ingestion-service

[sources.my_file_source]
  type = "file"
  ignore_older_secs = 86400
  include = ["/var/log/security-logs/*.log"]
  read_from = "beginning"

[transforms.json_parser]
  type = "remap"  # Vector's built-in transformation language
  inputs = ["my_file_source"]
  source = """
    # attempt to parse the log line as JSON, but fallback if invalid
    . = parse_json!(.message, drop_invalid = true) ?? .
  """

[sinks.ingestion_service]
  type            = "http"
  inputs          = ["json_parser"]
  uri             = "http://ingestion-service:5000/logs"  # Flask endpoint
  encoding.codec  = "json"

  # Optional for reliability:
  healthcheck.enabled = true
  request.in_flight_limit = 25
  request.rate_limit_num = 5
  request.retry_attempts = 10
  request.timeout_secs = 30
```

Key points:

• The “file” source monitors local logs.  
• A “remap” transform attempts to parse each line as JSON.  
• The “http” sink sends events to our ingestion-service at `http://ingestion-service:5000/logs`.  

This aligns with the approach described in our [Detailed Design Document](../docs/design-docs/detailed-design.md#3-detailed-components-and-responsibilities) under “Ingestion Service.”

---

## 6. Integration Workflow

1. **Local Testing**  
   - Start Vector in Docker (see snippet above).  
   - Ensure your ingestion-service is reachable at “http://ingestion-service:5000/logs” or whichever port you used.  
   - Tail the logs for both containers to confirm data flow:

   ```bash
   docker-compose logs -f vector
   docker-compose logs -f ingestion-service
   ```

2. **Data Validation**  
   - Check if your ingestion-service (Flask) receives valid JSON payloads from Vector.  
   - If parsing fails, update the `[transforms.json_parser]` or create new transforms that suit your log format.

3. **Performance Tuning**  
   - Vector is known for high throughput. If you handle large volumes of logs, consider advanced transforms like filtering or `log_to_metric` from Vector to manage data volume.  
   - Evaluate the concurrency or buffering parameters in Vector.  
   - For broader system scaling (message queues, classification concurrency), revisit the [detailed_backend_design_doc.md](../docs/design-docs/detailed_backend_design_doc.md.md#6-scalability-considerations).

4. **Persistent Storage**  
   - Optional: Instead of sending logs directly to ingestion-service, you can store them in a queue (e.g., RabbitMQ, Kafka) if you anticipate spikes. Vector can have a “kafka” sink or “socket” sink as well.  
   - Our ingestion-service can then read from that queue. This approach decouples ingestion from classification.

---

## 7. Deployment Considerations

### 7.1 Containerizing at Scale

• In production, you might deploy Vector as a DaemonSet on each Kubernetes node, so that logs are captured from all containers on that node, then forwarded to your ingestion-service or classification-service.  
• Check Vector’s [official Helm chart or K8s guide](https://github.com/vectordotdev/vector/tree/master/distribution/kubernetes) for references.

### 7.2 Security & Observability

• Use TLS if sending logs across untrusted networks (Vector supports `tls` settings for HTTP sinks).  
• Enable Vector’s [internal_metrics](https://github.com/vectordotdev/vector/blob/master/docs) if you want to ship metrics about pipeline performance to services like Prometheus or ClickHouse.  
• Consult our [tech_stack.md](../docs/design-docs/tech_stack.md) for references on environment variables and secrets management in Docker Compose.

---

## 8. Extending the Pipeline for OCSF Classification

After logs pass through Vector and reach the ingestion-service, they follow the pipeline steps described in the [Detailed Design Document](../docs/design-docs/detailed-design.md#4-data-flow-example). Summarizing:

1. ingestion-service normalizes them and might queue or forward them to classification-service.  
2. classification-service uses your knowledge base + optional RAG approach (Trieve or local DB) to map logs to OCSF classes.  
3. The result is stored in a data store like ClickHouse or logged for real-time analysis.

By ensuring that Vector reliably funnels logs into the pipeline, the rest of the classification, cross-encoder re-ranking, or Trieve integration remains consistent.

---

## 9. Troubleshooting & Best Practices

1. **Logs Not Reaching Ingestion-Service**  
   - Check endpoints: Vector config points to “http://ingestion-service:5000/logs”, but your ingestion-service might run on port 8080 or differ by environment.  
   - Ensure your Docker networks or Kubernetes services are bridging properly.

2. **High CPU Usage**  
   - Compare Vector’s performance to other log collectors. Often, Vector is more efficient, but if you run complex transforms (e.g., heavy Regex parsing), consider distributing the load or refining the transforms.

3. **File Rotation**  
   - By default, Vector tracks file positions in a checkpoint file. Familiarize yourself with [Vector’s file source docs](https://github.com/vectordotdev/vector/tree/master/docs#reference) to handle rotating logs effectively.

4. **Additional Sources**  
   - If you have use cases for syslog, journald, or Docker logs, simply add corresponding sections in `vector.toml`. The data still flows to our ingestion-service or message queue with minimal changes.

---

## 10. Summary & Next Steps

• Vector.dev seamlessly integrates with our backend microservices to gather logs at scale, unify their formats, and deliver them to our ingestion pipeline.  
• Start with the sample Docker Compose and `vector.toml` config, ensuring data flows from your environment to our ingestion-service.  
• Once stable, expand with more transforms, additional sources, or advanced buffering.  
• For final log classification and storing chunk data, proceed with the normal pipeline references in the [Detailed Design Document](../docs/design-docs/detailed-design.md).

Proceed to fine-tune your classification logic, incorporate our “Knowledge Base,” and if desired, add [Trieve Integration](../docs/design-docs/trieve_integration_guide.md) after verifying that Vector is reliably delivering logs where they need to go.

---

*(For more details, consult the official [Vector GitHub repository](https://github.com/vectordotdev/vector) and our detailed_backend_design_doc.md.”)*
```

