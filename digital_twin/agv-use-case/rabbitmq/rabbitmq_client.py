"""
RabbitMQ client for Simulation Bridge (interactive MATLAB AGV demo)

- Sends a simulation request to the Bridge
- Streams dynamic inputs (target/speed_cap/load_kg) to the Bridge
- Listens for results and stops streaming on 'completed'
- Streams live telemetry to a matplotlib visualizer (dt_visualizer.py)

IMPORTANT:
- Pika's BlockingConnection is NOT thread-safe. We use SEPARATE
  connections: one for the listener thread, one for publishing/streaming.

Config file expected: rabbitmq_use.yaml
Payload file expected: simulation.yaml
"""

import os
import ssl
import sys
import threading
import uuid
import time
from typing import Any, Dict, Optional

import pika
import yaml

# <<< NEW: live visualizer >>>
try:
    from dt_visualizer import start_visualizer, send_to_visualizer, stop_visualizer
except Exception as _e:
    start_visualizer = None
    send_to_visualizer = None
    stop_visualizer = None
    print("[VIS] Warning: dt_visualizer not available or failed to import. Visualization disabled.", file=sys.stderr)


# --------------------------- Config helpers ---------------------------

def load_config(config_path: str = "rabbitmq_use.yaml") -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as err:
        print(f"Error parsing YAML file: {err}")
        sys.exit(1)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ------------------------ Connection factory --------------------------

def _build_parameters(rabbitmq_cfg: Dict[str, Any]) -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(
        username=rabbitmq_cfg["username"],
        password=rabbitmq_cfg["password"],
    )
    use_tls = bool(rabbitmq_cfg.get("tls", False))

    if use_tls:
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_options = pika.SSLOptions(context, rabbitmq_cfg["host"])
        return pika.ConnectionParameters(
            host=rabbitmq_cfg["host"],
            port=rabbitmq_cfg.get("port", 5671),
            virtual_host=rabbitmq_cfg.get("vhost", "/"),
            credentials=credentials,
            ssl_options=ssl_options,
            heartbeat=rabbitmq_cfg.get("heartbeat", 600),
        )
    else:
        return pika.ConnectionParameters(
            host=rabbitmq_cfg["host"],
            port=rabbitmq_cfg.get("port", 5672),
            virtual_host=rabbitmq_cfg.get("vhost", "/"),
            credentials=credentials,
            heartbeat=rabbitmq_cfg.get("heartbeat", 600),
        )


# --------------------------- Client class -----------------------------

class RabbitMQClient:
    """Digital Twin client for Simulation Bridge (single-thread use)."""

    def __init__(self, config: Dict[str, Any], vis_queue=None) -> None:
        self.config = config
        self.dt_id: str = config["digital_twin"]["dt_id"]

        # connection/channel confined to this instance's thread
        params = _build_parameters(config["rabbitmq"])
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        # runtime/shared (per instance)
        self.result_queue_name: Optional[str] = None
        self.stream_exchange_name: Optional[str] = None

        # visualizer queue (optional)
        self.vis_queue = vis_queue

        self._setup_infrastructure()

    # -------------------- Setup --------------------

    def _setup_infrastructure(self) -> None:
        """Declare exchanges/queues/bindings."""
        exchanges = self.config["exchanges"]
        queue_cfg = self.config["queue"]

        # Exchanges
        self.channel.exchange_declare(
            exchange=exchanges["input_bridge"]["name"],
            exchange_type=exchanges["input_bridge"]["type"],
            durable=exchanges["input_bridge"]["durable"],
        )
        self.channel.exchange_declare(
            exchange=exchanges["bridge_result"]["name"],
            exchange_type=exchanges["bridge_result"]["type"],
            durable=exchanges["bridge_result"]["durable"],
        )

        # Optional stream exchange for interactive inputs
        input_stream_ex = exchanges.get("input_stream")
        if input_stream_ex:
            self.channel.exchange_declare(
                exchange=input_stream_ex["name"],
                exchange_type=input_stream_ex["type"],
                durable=input_stream_ex["durable"],
            )
            self.stream_exchange_name = input_stream_ex["name"]

        # Result queue/binding
        self.result_queue_name = f"{queue_cfg['result_queue_prefix']}.{self.dt_id}.result"
        self.channel.queue_declare(queue=self.result_queue_name, durable=queue_cfg["durable"])
        self.channel.queue_bind(
            exchange=exchanges["bridge_result"]["name"],
            queue=self.result_queue_name,
            routing_key=queue_cfg["routing_key"],
        )

    # -------------------- Bridge request --------------------

    def send_simulation_request(self, payload: Dict[str, Any]) -> str:
        """
        Send the simulation request to the Bridge and return the request_id used.
        Ensures simulation.request_id and bridge_meta.protocol are set.
        """
        sim = payload.setdefault("simulation", {})
        request_id = sim.get("request_id") or str(uuid.uuid4())
        sim["request_id"] = request_id
        sim.setdefault("bridge_meta", {})["protocol"] = "rabbitmq"

        routing_key = self.config["digital_twin"]["routing_key_send"]
        exchange_name = self.config["exchanges"]["input_bridge"]["name"]

        body = yaml.dump(payload, default_flow_style=False).encode("utf-8")
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/x-yaml",
                message_id=str(uuid.uuid4()),
            ),
        )
        print(f"[INIT] Sent simulation request (rk='{routing_key}') request_id={request_id}")
        return request_id

    # -------------------- Streaming inputs --------------------

    def publish_stream_frame(self, routing_key: str, request_id: str, inputs: Dict[str, Any]) -> None:
        """
        Publish a single dynamic-input frame to the Bridge (interactive mode).
        Format:
        simulation:
          request_id: <uuid>
          inputs: {...}
        """
        if not self.stream_exchange_name:
            print("[STREAM] No stream exchange configured. Skip.")
            return
        frame = {
            "simulation": {
                "request_id": request_id,
                "inputs": inputs or {},
            }
        }
        body = yaml.dump(frame).encode("utf-8")
        self.channel.basic_publish(
            exchange=self.stream_exchange_name,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/x-yaml",
                message_id=str(uuid.uuid4()),
            ),
        )

    # -------------------- Results consumer --------------------

    def start_listening(self, stop_event: threading.Event) -> None:
        """
        Start consuming results (blocking). If a message with status=completed arrives,
        sets stop_event to allow the publisher to stop streaming.
        Also forwards frames to the live visualizer (if available).
        """
        assert self.result_queue_name, "Result queue not initialized"

        def _on_message(ch, method, props, body):
            try:
                source = method.routing_key.split(".")[0]
                result = yaml.safe_load(body)

                print(f"\n[{self.dt_id.upper()}] Received result from {source}:")
                print(f"Result: {result}")
                print("-" * 50)

                # ---- forward to visualizer ----
                if self.vis_queue and isinstance(result, dict):
                    out = result.get("output", {})
                    if out:
                        payload = {
                            "sim_time": out.get("sim_time"),
                            "x": ((out.get("pose") or {}).get("x")),
                            "y": ((out.get("pose") or {}).get("y")),
                            "theta": ((out.get("pose") or {}).get("theta")),
                            "tx": ((out.get("target") or {}).get("x")),
                            "ty": ((out.get("target") or {}).get("y")),
                            "v": out.get("v"),
                            "soc": out.get("battery_soc"),
                            "reached": out.get("reached_waypoint"),
                            "agv_id": out.get("agv_id"),
                        }
                        try:
                            send_to_visualizer(self.vis_queue, payload)
                        except Exception as e:
                            print(f"[VIS] Failed to send to visualizer: {e}", file=sys.stderr)

                # Stop streaming on global 'completed'
                if isinstance(result, dict) and result.get("status") == "completed":
                    stop_event.set()
                    if self.vis_queue:
                        try:
                            stop_visualizer(self.vis_queue)
                        except Exception:
                            pass

                ch.basic_ack(method.delivery_tag)
            except yaml.YAMLError as err:
                print(f"Error decoding YAML result: {err}")
                ch.basic_nack(method.delivery_tag)
            except Exception as err:  # noqa: BLE001
                print(f"Error processing the result: {err}")
                ch.basic_nack(method.delivery_tag)

        self.channel.basic_consume(queue=self.result_queue_name, on_message_callback=_on_message)
        print(f"[{self.dt_id.upper()}] Listening for simulation results...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            pass
        finally:
            try:
                if self.channel.is_open:
                    self.channel.close()
            except Exception:
                pass
            try:
                if self.connection.is_open:
                    self.connection.close()
            except Exception:
                pass


# --------------------------- Streaming loop ---------------------------

def run_stream_loop(config: Dict[str, Any], request_id: str, stop_event: threading.Event) -> None:
    """
    Runs in the main thread: publishes dynamic inputs periodically until stop_event is set.
    Uses its own connection (separate from listener thread).
    """
    dt = RabbitMQClient(config)  # no vis queue needed for publisher

    payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                config.get("payload_file", "simulation.yaml"))
    payload = load_yaml_file(payload_path)
    sim = payload.get("simulation", {})
    if sim.get("type") != "interactive":
        print("[STREAM] Simulation is not interactive. Nothing to stream.")
        return

    stream_source = sim.get("inputs", {}).get("stream_source", "")
    stream_key = stream_source.replace("rabbitmq://", "")
    inputs_cfg = sim.get("inputs", {})

    # Script parameters
    script = (inputs_cfg or {}).get("script", {})
    waypoints = script.get("waypoints", [[0.0, 0.0], [3.0, 2.0], [6.0, 4.0], [0.0, 4.0]])
    dwell_s = float(script.get("dwell_s", 15.0))
    load_kg = script.get("load_kg", None)
    speed_caps = sorted(script.get("speed_caps", []), key=lambda ev: ev.get("at", 0.0))
    initial = (inputs_cfg or {}).get("initial", {})
    max_duration_s = float(script.get("max_duration_s", initial.get("DT", 0.1) * initial.get("MAX_STEPS", 2000)))

    start = time.monotonic()
    last_wp_idx = None
    sent_speed_idx = -1
    heartbeat_s = 2.0
    last_sent_time = 0.0

    # initial frame
    if waypoints:
        x0, y0 = waypoints[0]
    else:
        x0, y0 = 0.0, 0.0

    init_inputs = {"target": {"x": float(x0), "y": float(y0)}}
    if load_kg is not None:
        init_inputs["load_kg"] = float(load_kg)
    if speed_caps and abs(float(speed_caps[0].get("at", 0.0))) < 1e-6:
        init_inputs["speed_cap"] = float(speed_caps[0]["value"])
        sent_speed_idx = 0

    dt.publish_stream_frame(stream_key, request_id, init_inputs)
    last_sent_time = 0.0
    last_wp_idx = 0
    print(f"[STREAM] init target=({x0:.2f},{y0:.2f})")

    try:
        while not stop_event.is_set():
            elapsed = time.monotonic() - start
            if elapsed >= max_duration_s:
                print("[STREAM] max_duration_s reached. stopping stream.")
                break

            # waypoint change based on dwell_s (wall-clock)
            wp_idx = int(elapsed // dwell_s) % len(waypoints) if (dwell_s > 1e-6 and waypoints) else 0
            if waypoints and (last_wp_idx is None or wp_idx != last_wp_idx):
                tx, ty = waypoints[wp_idx]
                dt.publish_stream_frame(stream_key, request_id, {"target": {"x": float(tx), "y": float(ty)}})
                print(f"[STREAM] target -> ({tx:.2f},{ty:.2f}) @ {elapsed:.1f}s")
                last_wp_idx = wp_idx
                last_sent_time = elapsed

            # scheduled speed_cap events
            if (sent_speed_idx + 1) < len(speed_caps):
                ev = speed_caps[sent_speed_idx + 1]
                if elapsed >= float(ev.get("at", 0.0)):
                    dt.publish_stream_frame(stream_key, request_id, {"speed_cap": float(ev["value"])})
                    print(f"[STREAM] speed_cap -> {ev['value']} @ {elapsed:.1f}s")
                    sent_speed_idx += 1
                    last_sent_time = elapsed

            # heartbeat no-op (keep alive)
            if (elapsed - last_sent_time) >= heartbeat_s:
                dt.publish_stream_frame(stream_key, request_id, {})
                last_sent_time = elapsed

            time.sleep(0.1)
    finally:
        try:
            if dt.channel.is_open:
                dt.channel.close()
        except Exception:
            pass
        try:
            if dt.connection.is_open:
                dt.connection.close()
        except Exception:
            pass
        print("[STREAM] loop finished.")


# --------------------------- Main ------------------------------------

def main() -> None:
    config = load_config()

    # --- start visualizer process (optional) ---
    vis_proc = None
    vis_queue = None
    if start_visualizer is not None:
        try:
            vis_proc, vis_queue = start_visualizer(window_title="Simulation Bridge – AGV Live")
            print("[VIS] Visualizer started.")
        except Exception as e:
            print(f"[VIS] Failed to start visualizer: {e}", file=sys.stderr)
            vis_proc, vis_queue = None, None

    # Publisher connection for initial request
    publisher = RabbitMQClient(config)  # no queue needed for this instance

    # Load payload and send the simulation request
    payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                config.get("payload_file", "simulation.yaml"))
    payload = load_yaml_file(payload_path)
    request_id = publisher.send_simulation_request(payload)

    # Prepare a stop_event shared between threads
    stop_event = threading.Event()

    # Start a dedicated listener thread (with its OWN connection)
    def _listener():
        listener_client = RabbitMQClient(config, vis_queue=vis_queue)
        listener_client.start_listening(stop_event)

    listener_thread = threading.Thread(target=_listener, daemon=True)
    listener_thread.start()

    # If interactive, start streaming loop in MAIN thread (own connection inside the loop)
    sim = payload.get("simulation", {})
    if sim.get("type") == "interactive":
        # close the publisher's connection before starting the stream loop
        try:
            if publisher.channel.is_open:
                publisher.channel.close()
        except Exception:
            pass
        try:
            if publisher.connection.is_open:
                publisher.connection.close()
        except Exception:
            pass

        run_stream_loop(config, request_id, stop_event)
    else:
        # not interactive; close publisher connection and just wait for results
        try:
            if publisher.channel.is_open:
                publisher.channel.close()
        except Exception:
            pass
        try:
            if publisher.connection.is_open:
                publisher.connection.close()
        except Exception:
            pass

    print("\nPress Ctrl+C to terminate the program...")
    try:
        while listener_thread.is_alive():
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nProgram terminated by the user.")
        stop_event.set()
    finally:
        # ensure visualizer stops
        if vis_queue and stop_visualizer:
            try:
                stop_visualizer(vis_queue)
            except Exception:
                pass
        if vis_proc:
            try:
                vis_proc.join(timeout=2.0)
            except Exception:
                pass


if __name__ == "__main__":
    main()
