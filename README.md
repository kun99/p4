# P4

P4 - Saga Choreography Pattern

```bash
cd k8s
kubectl apply -f . 
```
## Requirements met

- Think all the requirements were met except for using OpenTelemetry for tracing.

##

## Expectations

- When an api call is made, the SEC initiates the transaction and publishes an event that runs the first microservice.
- Microservices are started by event messages and publish event messages when they are done.
- SEC picks up events published by microservices and publish a appropriate event message to start the next microservice until the transaction is complete.
- Rollbacks are initiated when a microservice fails through events.

##
