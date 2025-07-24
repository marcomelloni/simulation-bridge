# Thread Management in the MATLAB Agent

The agent separates RabbitMQ communication from MATLAB execution using a simple thread model. All RabbitMQ I/O occurs on a single consumer thread while each simulation runs in its own worker thread. This prevents thread‑safety problems in `pika` and allows the agent to interrupt simulations without blocking message handling.

## Consumer (I/O) Thread

`RabbitMQManager.start_consuming()` is called from the main thread of the agent. The method stores the thread that invokes it as the **I/O thread** and starts `pika`'s blocking consumption loop. Because `pika.BlockingConnection` is not thread safe, every publish must happen on this same thread.

`RabbitMQManager.send_message()` checks whether the current thread matches the stored I/O thread. If a worker thread needs to publish a message, the method schedules the publish with `connection.add_callback_threadsafe()`. The callback is then executed on the consumer thread so all RabbitMQ operations are serialized on the connection.

## Simulation Threads

`MessageHandler` creates a concrete implementation of the `MatlabSimulator` interface whenever a new message arrives. The available implementations are `BatchSimulator`, `StreamingSimulator` and `InteractiveSimulator`. Calling `start()` on any simulator launches a new daemon thread and invokes its private `_execute()` method.

The simulator thread performs the MATLAB computation and uses `RabbitMQManager.send_result()` to report progress or final data. Because `send_result()` relies on `send_message()` the actual publish always occurs on the I/O thread.

Interactive simulations also need to read frames from RabbitMQ while running. To avoid sharing the consumer connection across threads the interactive controller opens a dedicated `BlockingConnection` inside its thread. Results are still published through the manager so they follow the same safe path.

## Active Simulator and Stopping

`MessageHandler` stores the currently running simulator instance in `active_simulator`. Only one simulator can run at a time. When a `STOP` command is received the handler calls `active_simulator.stop()` which clears an internal event. Each `_execute()` loop checks this flag and exits when it is cleared. This mechanism provides a cooperative way to terminate simulations without abruptly killing threads.

