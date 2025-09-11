"""
simulation_bridge_router.py

Unisce i due client:
- LISTEN: consuma i risultati di Simulation Bridge (ex.sim.result) provenienti da AnyLogic
- ROUTE: se il campo 'data' contiene JSON con {"type":"SIM_INPUT","inputs":{...}}
         li trasforma in un frame YAML e li pubblica su ex.input.stream (routing key del flusso MATLAB)

Opzionale (--send-matlab-request): invia anche la richiesta iniziale a MATLAB (simulation.yaml).

CONFIG attesa (rabbitmq_use.yaml di default):

rabbitmq:
  host: localhost
  port: 5672
  vhost: /
  username: guest
  password: guest
  heartbeat: 600
  tls: false

digital_twin:
  dt_id: dt_anylogic

queue:
  result_queue_prefix: Q
  durable: true
  routing_key: "anylogic.result.dt_anylogic"     # binding key per ex.sim.result

exchanges:
  bridge_result:
    name: "ex.sim.result"
    type: "topic"
    durable: true
  input_stream:
    name: "ex.input.stream"
    type: "topic"
    durable: true
  input_bridge:
    name: "ex.bridge.output"                     # usato SOLO se --send-matlab-request
    type: "topic"
    durable: true

stream:                                          # destinazione per MATLAB interactive inputs
  routing_key: "streaming.inputs.sim123"         # es. come nei tuoi esempi
  request_id: ""                                 # opzionale; se vuoto viene generato UUID

files:
  payload: "simulation.yaml"                     # usato SOLO se --send-matlab-request
"""
# top of simulation_bridge_router.py
try:
    from dt_visualizer import start_visualizer, send_to_visualizer, stop_visualizer
except Exception as e:
    start_visualizer = None
    send_to_visualizer = None
    stop_visualizer = None
    print(f"[VIS] Warning: visualizer not available ({e})")

import argparse
import json
import os
import ssl
import sys
import uuid
from typing import Any, Dict, Optional

import pika
import yaml


# --------------------------- Helpers ---------------------------

def load_config(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: configuration '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as err:
        print(f"YAML error in '{path}': {err}", file=sys.stderr)
        sys.exit(1)


def build_params(rmq: Dict[str, Any]) -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(
        rmq.get("username", "guest"),
        rmq.get("password", "guest"),
    )
    use_tls = bool(rmq.get("tls", False))
    port = rmq.get("port", 5671 if use_tls else 5672)
    ssl_options = None
    if use_tls:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_options = pika.SSLOptions(ctx, rmq.get("host", "localhost"))
    return pika.ConnectionParameters(
        host=rmq.get("host", "localhost"),
        port=port,
        virtual_host=rmq.get("vhost", "/"),
        credentials=credentials,
        heartbeat=rmq.get("heartbeat", 600),
        ssl_options=ssl_options,
    )


# --------------------------- Router client ---------------------------

class Router:
    """
    - Consuma messaggi da ex.sim.result (binding key dal config.queue.routing_key)
    - Filtra quelli con result['data'] = JSON con {"type":"SIM_INPUT","inputs":{...}}
    - Pubblica su ex.input.stream con YAML:
        simulation:
          request_id: <...>
          inputs: { ... }
    - (opzionale) invia la richiesta iniziale a MATLAB (simulation.yaml) su ex.bridge.output
    """

    def __init__(self, cfg: Dict[str, Any], send_matlab_request: bool) -> None:
        self.cfg = cfg
        self.dt_id: str = cfg["digital_twin"]["dt_id"]
        self.ex_result = cfg["exchanges"]["bridge_result"]
        self.ex_stream = cfg["exchanges"]["input_stream"]
        
        # start visualizer if available
        self.vis_proc, self.vis_queue = None, None
        if start_visualizer:
            try:
                self.vis_proc, self.vis_queue = start_visualizer("Simulation Bridge – AGV Live")
                print("[VIS] Visualizer started.")
            except Exception as e:
                print(f"[VIS] Failed to start visualizer: {e}")


        # stream routing key e request_id per la sessione MATLAB
        stream_cfg = cfg.get("stream", {})
        self.stream_rk: str = stream_cfg.get("routing_key", "streaming.inputs.sim123")
        self.request_id: str = stream_cfg.get("request_id") or str(uuid.uuid4())

        # --- connessione principale ---
        params = build_params(cfg["rabbitmq"])
        self.conn = pika.BlockingConnection(params)
        self.ch = self.conn.channel()

        # Dichiara exchanges/queue per i risultati
        self._setup_infra()

        # Publisher dedicato per stream (stessa connessione/chan va bene qui)
        # se si preferisce, si può aprire una channel separata:
        self.stream_exchange_name = self.ex_stream["name"]

        # opzionale: invio richiesta iniziale a MATLAB
        if send_matlab_request:
            self._maybe_send_matlab_request()

    def _setup_infra(self) -> None:
        # results exchange
        self.ch.exchange_declare(
            exchange=self.ex_result["name"],
            exchange_type=self.ex_result["type"],
            durable=self.ex_result["durable"],
        )
        # input stream exchange (per pubblicare)
        self.ch.exchange_declare(
            exchange=self.ex_stream["name"],
            exchange_type=self.ex_stream["type"],
            durable=self.ex_stream["durable"],
        )

        # result queue/binding
        qcfg = self.cfg["queue"]
        self.result_queue = f"{qcfg['result_queue_prefix']}.{self.dt_id}.result"
        self.ch.queue_declare(queue=self.result_queue, durable=qcfg["durable"])
        self.ch.queue_bind(
            exchange=self.ex_result["name"],
            queue=self.result_queue,
            routing_key=qcfg["routing_key"],
        )
        print(f"[ROUTER] Listening on '{self.ex_result['name']}' "
              f"rk='{qcfg['routing_key']}', queue='{self.result_queue}'")

    def _maybe_send_matlab_request(self) -> None:
        try:
            ex_bridge = self.cfg["exchanges"]["input_bridge"]
            self.ch.exchange_declare(
                exchange=ex_bridge["name"],
                exchange_type=ex_bridge["type"],
                durable=ex_bridge["durable"],
            )
            payload_path = self.cfg.get("payload_file", "simulation.yaml")
            with open(payload_path, "r", encoding="utf-8") as f:
                payload = yaml.safe_load(f)

            # imposta request_id e meta
            sim = payload.setdefault("simulation", {})
            sim["request_id"] = self.request_id
            sim.setdefault("bridge_meta", {})["protocol"] = "rabbitmq"

            rk_send = self.cfg["digital_twin"].get("routing_key_send", "dt.matlab")
            body = yaml.dump(payload, default_flow_style=False).encode("utf-8")

            self.ch.basic_publish(
                exchange=ex_bridge["name"],
                routing_key=rk_send,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/x-yaml",
                    message_id=str(uuid.uuid4()),
                ),
            )
            print(f"[ROUTER] Sent MATLAB request (rk='{rk_send}') request_id={self.request_id}")
        except Exception as e:
            print(f"[ROUTER] Warning: failed to send MATLAB request: {e}", file=sys.stderr)

    # ----------------- consume & route -----------------

    def _publish_stream_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Pubblica su ex.input.stream un frame YAML:
          simulation:
            request_id: <self.request_id>
            inputs: { ... }
        """
        frame = {
            "simulation": {
                "request_id": self.request_id,
                "inputs": inputs or {},
            }
        }
        body = yaml.dump(frame, default_flow_style=False).encode("utf-8")
        self.ch.basic_publish(
            exchange=self.stream_exchange_name,
            routing_key=self.stream_rk,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/x-yaml",
                message_id=str(uuid.uuid4()),
            ),
        )
        print(f"[ROUTER] → streamed inputs to '{self.stream_rk}': {inputs}")

    def _handle_result(self, ch, method, _props, body):  # noqa: N802
        try:
            result = yaml.safe_load(body)
            source = method.routing_key.split(".")[0]
            print(f"\n[ROUTER] Result from {source}:")
            print(result)
            print("-" * 40)

            # 1) Se c'è un campo 'data' JSON, parse
            inputs_forwarded = False
            # --- Forward telemetry frames to visualizer ---
            if isinstance(result, dict) and "data" in result:
                try:
                    data_obj = json.loads(result["data"])
                    # SIM_INPUT → già gestito sopra
                    if isinstance(data_obj, dict) and data_obj.get("output"):
                        out = data_obj["output"]
                        payload = {
                            "sim_time": out.get("sim_time"),
                            "x": (out.get("pose") or {}).get("x"),
                            "y": (out.get("pose") or {}).get("y"),
                            "theta": (out.get("pose") or {}).get("theta"),
                            "tx": (out.get("target") or {}).get("x"),
                            "ty": (out.get("target") or {}).get("y"),
                            "v": out.get("v"),
                            "soc": out.get("battery_soc"),
                            "reached": out.get("reached_waypoint"),
                            "agv_id": out.get("agv_id"),
                        }
                        if self.vis_queue and send_to_visualizer:
                            send_to_visualizer(self.vis_queue, payload)
                except Exception:
                    pass


            # (facoltativo) se vuoi trattare anche telemetria, puoi intercettarla qui
            if not inputs_forwarded:
                # solo log, nessun inoltro
                pass

            ch.basic_ack(method.delivery_tag)

            # 2) termina se lo status globale è 'completed'
            if isinstance(result, dict) and result.get("status") == "completed":
                print("[ROUTER] Completed. Exiting…")
                self.shutdown()
        except Exception as exc:  # noqa: BLE001
            print(f"[ROUTER] Error processing result: {exc}", file=sys.stderr)
            ch.basic_nack(method.delivery_tag)

    def start(self) -> None:
        self.ch.basic_consume(queue=self.result_queue, on_message_callback=self._handle_result)
        try:
            print("[ROUTER] Waiting for AnyLogic → SIM_INPUT …")
            self.ch.start_consuming()
        except KeyboardInterrupt:
            print("\n[ROUTER] Interrupted by user.")
            self.shutdown()
        except Exception as exc:  # noqa: BLE001
            print(f"[ROUTER] Unexpected error: {exc}", file=sys.stderr)
            self.shutdown(code=1)

    def shutdown(self, code: int = 0) -> None:
        try:
            if self.ch.is_open:
                self.ch.stop_consuming()
        except Exception:
            pass
        try:
            if self.conn.is_open:
                self.conn.close()
        except Exception:
            pass
        try:
            # stop visualizer on exit
            if self.vis_queue and stop_visualizer:
                try:
                    stop_visualizer(self.vis_queue)
                except Exception:
                    pass
            if self.vis_proc:
                try:
                    self.vis_proc.join(timeout=2.0)
                except Exception:
                    pass
        except Exception:
            pass
        sys.exit(code)


# --------------------------- main ---------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Route AnyLogic SIM_INPUTs to MATLAB stream via Simulation Bridge")
    ap.add_argument("-c", "--config", default="rabbitmq_use.yaml", help="Path to YAML config")
    ap.add_argument("--send-matlab-request", action="store_true",
                    help="Also send the initial MATLAB request (simulation.yaml from config.files.payload)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    router = Router(cfg, send_matlab_request=args.send_matlab_request)
    router.start()


if __name__ == "__main__":
    main()
