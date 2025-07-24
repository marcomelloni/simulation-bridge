# Thread Management in the MATLAB Agent

The MATLAB agent relies on a dedicated thread to handle RabbitMQ I/O while simulations run in their own worker threads. This separation avoids thread safety issues with `pika` and allows the agent to interrupt simulations cleanly.

## Consumer Thread

When `RabbitMQManager.start_consuming` is invoked, the calling thread becomes the **I/O thread**. Every message received from RabbitMQ is processed on this thread. Because `pika.BlockingConnection` is not thread safe, any publish operation must occur on this same thread.

`RabbitMQManager.send_message` checks the current thread against the stored I/O thread. If a different thread needs to publish a message (for example from a running simulation), the method schedules the publish with `connection.add_callback_threadsafe`. This guarantees that all communication with RabbitMQ happens on the consumer thread.

## Simulation Threads

`MessageHandler` creates an instance of `BatchSimulator`, `StreamingSimulator` or `InteractiveSimulator` depending on the message type. Each simulator implements the common `MatlabSimulator` interface. Calling `start()` launches a new thread where the simulator executes its `_execute` logic.

The simulator thread performs the MATLAB work and uses the broker to publish results. Because `send_message` uses the callback mechanism described above, these results are sent safely through the consumer thread.

The handler stores a reference to the active simulator. It can call `stop()` in response to a `STOP` command to signal the thread to terminate. Only one simulator is active at a time, simplifying resource management.

## Stopping

A simulator sets an internal event when running. Calling `stop()` clears this event. The `_execute` loop in each implementation checks this flag and exits when it is cleared, ensuring that MATLAB executions can be interrupted without forcing the thread to stop abruptly.
