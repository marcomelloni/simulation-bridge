"""
simulation_bridge_listener.py

Listener-only RabbitMQ client for **Simulation Bridge**.
- Connects to RabbitMQ
- Binds a result queue
- Prints incoming results
- Exits automatically when a message with {"status": "completed"} is received.

Config file expected (default: rabbitmq_use.yaml) with keys:
rabbitmq:
  host: ...
  port: ...
  vhost: ...
  username: ...
  password: ...
  heartbeat: 600
  tls: false
digital_twin:
  dt_id: dt_anylogic     # used to name the result queue
queue:
  result_queue_prefix: Q
  durable: true
  routing_key: "matlab.result.dt_anylogic"   # binding key to results exchange
exchanges:
  bridge_result:
    name: "ex.sim.result"
    type: "topic"
    durable: true
"""

import argparse
import os
import ssl
import sys
import uuid
from typing import Any, Dict

import pika
import yaml


def load_config(path: str = "rabbitmq_use.yaml") -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: configuration file '{path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as err:
        print(f"Error parsing YAML in '{path}': {err}")
        sys.exit(1)


class SimulationBridgeListener:
    """Listener-only client for Simulation Bridge results."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.dt_id: str = config["digital_twin"]["dt_id"]

        # --- Build connection parameters (TLS or plain) ---
        rmq = config["rabbitmq"]
        credentials = pika.PlainCredentials(rmq.get("username", "guest"),
                                            rmq.get("password", "guest"))
        use_tls = bool(rmq.get("tls", False))
        port = rmq.get("port", 5671 if use_tls else 5672)

        ssl_options = None
        if use_tls:
            ctx = ssl.create_default_context()
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            ssl_options = pika.SSLOptions(ctx, rmq.get("host", "localhost"))

        params = pika.ConnectionParameters(
            host=rmq.get("host", "localhost"),
            port=port,
            virtual_host=rmq.get("vhost", "/"),
            credentials=credentials,
            heartbeat=rmq.get("heartbeat", 600),
            ssl_options=ssl_options,
        )

        # --- Connect & channel ---
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        # --- Declare/bind infrastructure ---
        self.result_queue = ""  # set in _setup_infrastructure
        self._setup_infrastructure()

    def _setup_infrastructure(self) -> None:
        ex_result = self.config["exchanges"]["bridge_result"]  # e.g., ex.sim.result
        queue_cfg = self.config["queue"]

        # Declare results exchange (idempotent)
        self.channel.exchange_declare(
            exchange=ex_result["name"],
            exchange_type=ex_result["type"],
            durable=ex_result["durable"],
        )

        # Declare & bind result queue for this DT
        self.result_queue = f"{queue_cfg['result_queue_prefix']}.{self.dt_id}.result"
        self.channel.queue_declare(queue=self.result_queue, durable=queue_cfg["durable"])
        self.channel.queue_bind(
            exchange=ex_result["name"],
            queue=self.result_queue,
            routing_key=queue_cfg["routing_key"],  # e.g., "matlab.result.dt_anylogic"
        )

        print(f"[{self.dt_id.upper()}] Bound queue '{self.result_queue}' "
              f"to '{ex_result['name']}' with key '{queue_cfg['routing_key']}'.")

    # ------------- Consuming -------------

    def _handle_result(self, ch, method, _props, body):  # noqa: N802
        try:
            result = yaml.safe_load(body)
            source = method.routing_key.split(".")[0]  # best-effort (e.g., "matlab","anylogic")
            print(f"\n[{self.dt_id.upper()}] Result from {source}:")
            print(result)
            print("-" * 40)

            ch.basic_ack(method.delivery_tag)

            # Auto-exit on completed
            if isinstance(result, dict) and result.get("status") == "completed":
                print(f"[{self.dt_id.upper()}] Completed received. Shutting down…")
                self._shutdown()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Error processing result: {exc}")
            ch.basic_nack(method.delivery_tag)

    def start(self) -> None:
        print(f"[{self.dt_id.upper()}] Listening for Simulation Bridge results…")
        self.channel.basic_consume(queue=self.result_queue,
                                   on_message_callback=self._handle_result)
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            self._shutdown()
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Unexpected error: {exc}")
            self._shutdown(code=1)

    # ------------- Cleanup -------------

    def _shutdown(self, code: int = 0) -> None:
        try:
            if self.channel.is_open:
                self.channel.stop_consuming()
        except Exception:
            pass
        try:
            if self.connection.is_open:
                self.connection.close()
        except Exception:
            pass
        print(f"[{self.dt_id.upper()}] Connection closed. Exiting.")
        os._exit(code)  # ensure immediate exit for scripts


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulation Bridge listener-only client")
    parser.add_argument("--config", "-c", default="rabbitmq_use.yaml",
                        help="Path to YAML config (default: rabbitmq_use.yaml)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    listener = SimulationBridgeListener(cfg)
    listener.start()


if __name__ == "__main__":
    main()
