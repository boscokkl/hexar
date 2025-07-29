# Hexar Monitoring Setup

This directory contains monitoring configuration for the Hexar multi-agent system.

## Files

- `prometheus.yml` - Prometheus scraping configuration
- `alert_rules.yml` - Alerting rules for critical system metrics
- `docker-compose.monitoring.yml` - Extended monitoring stack (optional)

## Quick Start

The main `docker-compose.yml` includes Prometheus monitoring. To access:

1. **Prometheus UI**: http://localhost:9090
2. **Metrics Endpoints**:
   - Backend health: http://localhost:8000/health
   - Agent status: http://localhost:8000/agents/status  
   - Agent health: http://localhost:8000/agents/health
   - MCP status: http://localhost:8000/api/enhanced/system-status
   - Resource status: http://localhost:8000/resources/status

## Key Metrics Monitored

### System Health
- API response times and error rates
- Agent health scores and availability
- MCP message queue lengths
- Resource pool utilization
- Memory and CPU usage

### Agent Performance
- Search query completion times
- Vendor agent response rates
- Circuit breaker states
- Fallback strategy usage
- Cache hit rates

### MCP System
- Message broker statistics
- Agent registry status
- Coordination pattern success rates
- Load balancer metrics

## Alerts

The system monitors for:
- **Critical**: Multiple unhealthy agents, MCP system down, database issues
- **Warning**: High error rates, slow responses, circuit breakers open

## Integration

### Production Monitoring
For production deployments, consider:
- Grafana dashboards for visualization
- AlertManager for notification routing
- Remote write to managed Prometheus services
- Log aggregation with ELK stack

### Local Development
```bash
# Start with monitoring
docker-compose up -d

# View Prometheus targets
open http://localhost:9090/targets

# Check agent health
curl http://localhost:8000/agents/health | jq
```

## Custom Metrics

The backend exposes custom metrics at `/metrics` endpoint:
- `hexar_query_duration_seconds` - Query processing time
- `hexar_agents_total` - Total registered agents
- `hexar_agents_healthy` - Currently healthy agents
- `hexar_mcp_messages_total` - MCP messages processed
- `hexar_circuit_breaker_state` - Circuit breaker states

## Troubleshooting

### Common Issues
1. **Prometheus not scraping**: Check target health at `/targets`
2. **Missing metrics**: Ensure backend `/metrics` endpoint is accessible
3. **High memory usage**: Monitor resource pool metrics
4. **Agent failures**: Check individual agent health scores

### Debugging Commands
```bash
# Check Prometheus config
docker exec hexar-monitoring cat /etc/prometheus/prometheus.yml

# View current targets
curl http://localhost:9090/api/v1/targets

# Test metrics endpoint
curl http://localhost:8000/metrics
```