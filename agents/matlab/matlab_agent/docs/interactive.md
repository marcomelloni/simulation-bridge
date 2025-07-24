# Interactive Simulation

An interactive simulation exchanges small data frames with the MATLAB process while it is running. The agent keeps a persistent TCP connection to MATLAB and relays frames received from RabbitMQ to the process. Every response from MATLAB is sent back to the broker so that clients can consume it in real time.

## Frame Format

Each message flowing from the broker to the agent must be a YAML document of the form:

```yaml
simulation:
  inputs:
    <key>: <value>
```

The `inputs` section contains the parameters that will be provided to the MATLAB simulation step. Frames published by MATLAB follow the same structure but typically include additional fields describing the current state or a completion flag.

## Workflow

1. **Start** – When the agent receives an `interactive` simulation request it launches an `InteractiveSimulator` in a dedicated thread. The simulator starts two local TCP servers: one for sending data to MATLAB and one for receiving its outputs.
2. **Connection Setup** – The simulator opens its own `BlockingConnection` to RabbitMQ. A queue named `Q.<agent>.interactive.<request_id>` is declared and bound to the routing key defined in the simulation payload (`inputs.stream_source`).
3. **Handshake** – After starting MATLAB, the agent waits for the MATLAB process to connect to both TCP ports. A simple handshake is performed by sending an empty JSON object.
4. **Main Loop** – The simulator continuously polls the dedicated RabbitMQ connection for new frames. Received inputs are forwarded over the TCP socket to MATLAB. Any JSON messages coming from MATLAB are packaged into responses using `create_response` and published with `send_result`.
5. **Completion** – When MATLAB signals that the simulation is finished (for example by sending a frame with `status: completed`) the simulator publishes the final response, closes the TCP servers and its RabbitMQ connection, and exits.

This separation of connections ensures that no socket is shared between threads and allows the agent to stop the interactive simulation safely if requested.
