"""
use_matlab_agent_interactive.py

Asynchronous RabbitMQ client for sending interactive simulation requests
to the MATLAB agent
"""

import argparse
import asyncio
import ssl
import uuid
from typing import Any, Dict

import anyio
import yaml
from aio_pika import (
    connect_robust,
    ExchangeType,
    Message,
    DeliveryMode,
)


class InteractiveUsageMatlabAgent:
    """
    Asynchronous client that interacts with a MATLAB agent for running interactive simulations.
    This class connects to RabbitMQ, sends requests to the MATLAB agent, streams input frames,
    and processes the results.
    """

    def __init__(self, agent_id: str, destination_id: str,
                 rabbitmq_cfg: Dict[str, Any]) -> None:
        """
        Initializes the agent with necessary identifiers and configuration.
        Sets up the result queue for receiving simulation results.
        """
        self.agent_id = agent_id
        self.destination_id = destination_id
        self.cfg = rabbitmq_cfg
        # Queue to receive results
        self.result_queue = f"Q.{agent_id}.matlab.result"
        # Event to stop the stream when the simulation ends
        self.stop_event = asyncio.Event()

    async def setup(self) -> None:
        """
        Connects to RabbitMQ, declares necessary exchanges and queues for sending/receiving messages.
        This includes setting up TLS if enabled in the configuration.
        """
        tls_enabled: bool = bool(self.cfg.get("tls", False))
        # Default port is 5671 for TLS, 5672 otherwise
        port = self.cfg.get("port", 5671 if tls_enabled else 5672)

        ssl_ctx = None
        if tls_enabled:
            # Create SSL context if TLS is enabled
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2

        # Establish connection to RabbitMQ using the configuration settings
        self.connection = await connect_robust(
            host=self.cfg.get("host", "localhost"),
            port=port,
            virtualhost=self.cfg.get("vhost", "/"),
            login=self.cfg.get("username", "guest"),
            password=self.cfg.get("password", "guest"),
            heartbeat=self.cfg.get("heartbeat", 600),
            ssl=tls_enabled,  # Enable SSL if needed
        )

        self.channel = await self.connection.channel()  # Create a new channel
        # Set prefetch count to avoid overwhelming the consumer
        await self.channel.set_qos(prefetch_count=1)

        # Declare RabbitMQ exchanges for different types of communication
        self.ex_bridge = await self.channel.declare_exchange(
            "ex.bridge.output", ExchangeType.TOPIC, durable=True
        )
        self.ex_result = await self.channel.declare_exchange(
            "ex.sim.result", ExchangeType.TOPIC, durable=True
        )
        self.ex_stream = await self.channel.declare_exchange(
            "ex.input.stream", ExchangeType.TOPIC, durable=True
        )

        # Declare the result queue where the agent will receive simulation
        # results
        self.queue = await self.channel.declare_queue(
            self.result_queue, durable=True
        )
        await self.queue.bind(
            self.ex_result,
            routing_key=f"{self.destination_id}.result.{self.agent_id}",
        )

    async def send_initial_interactive_request(
        self, payload: Dict[str, Any], request_id: str
    ) -> None:
        """
        Sends the initial request to the MATLAB simulation. This includes necessary
        metadata and sets up the simulation environment.

        """
        payload["simulation"]["request_id"] = request_id
        payload["simulation"].setdefault("bridge_meta", {})[
            "protocol"] = "rabbitmq"

        routing_key = f"{self.agent_id}.{self.destination_id}"
        # Publish the request message to the bridge exchange
        await self.ex_bridge.publish(
            Message(
                body=yaml.dump(payload, default_flow_style=False).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,  # Ensure message is persistent
                content_type="application/x-yaml",  # Content type is YAML
                message_id=str(uuid.uuid4()),  # Unique ID for the message
            ),
            routing_key=routing_key,
        )
        print(
            f"[INIT] Sent interactive request (rk='{routing_key}') request_id={request_id}")

    async def stream_inputs(self, request_id: str, stream_key: str, inputs_cfg: Dict[str, Any]) -> None:
        """
        Pubblica frame dinamici per AGV_Simple.m:
          - target {x,y} a intervalli (dwell_s)
          - speed_cap ad orari prestabiliti
          - load_kg all'avvio (o quando cambia)
        """
        print(f"[INPUT STREAM] Publishing AGV frames on '{stream_key}' …")

        # ---- Leggi configurazione dallo YAML ----
        script = inputs_cfg.get("script", {}) if inputs_cfg else {}
        waypoints = script.get("waypoints", [[0.0, 0.0], [3.0, 2.0], [6.0, 4.0], [0.0, 4.0]])
        dwell_s = float(script.get("dwell_s", 15.0))
        load_kg = script.get("load_kg", None)
        speed_caps = script.get("speed_caps", [])
        max_duration_s = float(
            script.get(
                "max_duration_s",
                # fallback: DT*MAX_STEPS se disponibili negli initial
                (inputs_cfg.get("initial", {}).get("DT", 0.1)
                 * inputs_cfg.get("initial", {}).get("MAX_STEPS", 2000))
                if inputs_cfg else 120.0
            )
        )

        # Ordina eventi speed_cap per tempo
        speed_caps = sorted(speed_caps, key=lambda ev: ev.get("at", 0.0))

        # Helper per pubblicare un frame
        async def publish_inputs(payload_inputs: Dict[str, Any]) -> None:
            frame = {
                "simulation": {
                    "request_id": request_id,
                    "inputs": payload_inputs,
                }
            }
            await self.ex_stream.publish(
                Message(
                    body=yaml.dump(frame).encode(),
                    content_type="application/x-yaml",
                    message_id=str(uuid.uuid4()),
                ),
                routing_key=stream_key,
            )

        # Stato interno
        start = asyncio.get_event_loop().time()
        last_wp_idx = None
        sent_speed_idx = -1
        heartbeat_s = 2.0  # invia un noop periodico per evitare timeout wrapper (se serve)
        last_sent_time = 0.0

        # 1) invio iniziale: load_kg + primo target + eventuale speed_cap(t=0)
        if waypoints:
            x0, y0 = waypoints[0]
        else:
            x0, y0 = 0.0, 0.0

        init_inputs = {"target": {"x": float(x0), "y": float(y0)}}
        if load_kg is not None:
            init_inputs["load_kg"] = float(load_kg)
        # applica speed_cap iniziale se definita a t=0
        if speed_caps and abs(float(speed_caps[0].get("at", 0.0))) < 1e-6:
            init_inputs["speed_cap"] = float(speed_caps[0]["value"])
            sent_speed_idx = 0

        await publish_inputs(init_inputs)
        last_sent_time = 0.0
        last_wp_idx = 0

        # 2) loop principale
        while not self.stop_event.is_set():
            now = asyncio.get_event_loop().time()
            elapsed = now - start
            if elapsed >= max_duration_s:
                print("[INPUT STREAM] Reached max_duration_s, stopping input stream.")
                break

            # Waypoint corrente in base a dwell_s
            if dwell_s > 1e-6 and waypoints:
                wp_idx = int(elapsed // dwell_s) % len(waypoints)
            else:
                wp_idx = 0

            # Cambiamento waypoint?
            if waypoints and (last_wp_idx is None or wp_idx != last_wp_idx):
                tx, ty = waypoints[wp_idx]
                await publish_inputs({"target": {"x": float(tx), "y": float(ty)}})
                last_wp_idx = wp_idx
                last_sent_time = elapsed
                print(f"[INPUT STREAM] New target -> ({tx:.2f}, {ty:.2f}) @ {elapsed:.1f}s")

            # Eventi speed_cap schedulati
            if (sent_speed_idx + 1) < len(speed_caps):
                ev = speed_caps[sent_speed_idx + 1]
                if elapsed >= float(ev.get("at", 0.0)):
                    await publish_inputs({"speed_cap": float(ev["value"])})
                    sent_speed_idx += 1
                    last_sent_time = elapsed
                    print(f"[INPUT STREAM] speed_cap -> {ev['value']} @ {elapsed:.1f}s")

            # Heartbeat no-op (facoltativo): invia un frame vuoto per evitare timeout
            if (elapsed - last_sent_time) >= heartbeat_s:
                await publish_inputs({})  # nessun cambio, serve solo a mantenere vivo lo stream
                last_sent_time = elapsed

            await asyncio.sleep(0.1)  # respiro per la coda

        print("[INPUT STREAM] Input loop finished.")
        
    async def handle_results(self) -> None:
        """
        Consumes results asynchronously from the MATLAB simulation. When a result with status 'completed'
        is received, it stops the input stream.
        """
        async with self.queue.iterator() as q:
            async for msg in q:  # Continuously listen for incoming messages from the result queue
                async with msg.process():
                    result = yaml.safe_load(
                        msg.body)  # Parse the result message

                    print(f"\n[RESULT] {result}\n" + "-" * 40)

                    # Check if the simulation is completed
                    if isinstance(result, dict) and result.get(
                            "status") == "completed":
                        print("Received completion signal from MATLAB.")
                        self.stop_event.set()  # Set the stop event to end the input stream
                        break


async def main() -> None:
    """
    Main entry point for the script. Handles the command-line arguments,
    loads configuration and payload, and starts the simulation.
    """
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="MATLAB interactive client")
    parser.add_argument(
        "--config",
        "-c",
        default="use.yaml",
        help="YAML with RabbitMQ connection settings (default: use.yaml)",
    )
    parser.add_argument(
        "--api-payload",
        "-p",
        default="simulation.yaml",
        help="YAML simulation payload to send (default: simulation.yaml)",
    )
    args = parser.parse_args()

    # Load RabbitMQ configuration from the provided file
    async with await anyio.open_file(args.config, "r", encoding="utf-8") as f_cfg:
        rabbit_cfg = yaml.safe_load(await f_cfg.read()).get("rabbitmq", {})

    # Load the simulation payload from the provided file
    async with await anyio.open_file(args.api_payload, "r", encoding="utf-8") as f_pl:
        payload = yaml.safe_load(await f_pl.read())

    # Initialize the simulation client (here, it is MATLAB-specific)
    client = InteractiveUsageMatlabAgent("dt", "matlab", rabbit_cfg)

    request_id = str(uuid.uuid4())  # Unique request ID for this simulation
    # Input stream source (RabbitMQ URL)
    stream_source = payload["simulation"]["inputs"]["stream_source"]
    # Extract the routing key for the stream
    stream_key = stream_source.replace("rabbitmq://", "")
    inputs_cfg = payload["simulation"].get("inputs", {})

    # Setup and send the initial interactive request to MATLAB
    await client.setup()
    await client.send_initial_interactive_request(payload, request_id)

    # Run both result handler and input stream publisher concurrently
    await asyncio.gather(
        client.handle_results(),
        client.stream_inputs(request_id, stream_key, inputs_cfg),
    )

    print("Simulation client finished.")


if __name__ == "__main__":
    asyncio.run(main())
