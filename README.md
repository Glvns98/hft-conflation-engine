# hft-conflation-engine
An O(1) memory asynchronous conflation engine for high-frequency parallel market data. Prevents asyncio event-loop blocking and silent OOM crashes in streaming applications.


#Core Mechanics: Under the Hood

The engine replaces standard queuing with an atomic, event-driven state mechanism utilizing two primitives:

1. **`asyncio.Lock` (Zero-Data-Race Mutex):** Ensures that parallel streams writing to the memory dictionary at the exact same microsecond do not corrupt the state. The lock is held for mere nanoseconds—only long enough to overwrite a dictionary key—guaranteeing network ingestion is never blocked.
2. **`asyncio.Event` (CPU-Efficient Polling):** The strategy processor does not use `while True: await asyncio.sleep(0.01)` to check for updates. That burns CPU cycles. Instead, it waits on `asyncio.Event.wait()`. It remains entirely dormant, consuming 0% CPU, until a stream explicitly signals that fresh data has arrived.

## 📊 Performance Characteristics

* **Memory Complexity:** $O(N)$ where $N$ is the number of tracked symbols. Memory scales horizontally with the asset count, NOT vertically with the tick volume. Tracking 1 tick or 1,000,000 ticks consumes the exact same amount of RAM.
* **Latency Profile:** Designed for systems where network I/O outpaces execution logic. Intermediary ticks are discarded (conflated) locally, ensuring the processor operates purely on real-time state, eliminating execution slippage.
* **Concurrency:** Tested and optimized for 90+ parallel WebSocket streams running on a single asynchronous event loop without IPC overhead.

## 🔌 Production Integration 

To use this in production (e.g., with MetaTrader 5, Deriv API, or Binance WebSockets), simply replace the `symbol_stream` mock with your actual connection handler. 

The engine is agnostic to your data source. Just call `engine.ingest_tick()` inside your `on_message` callback:

```python
async def real_websocket_handler(symbol: str, engine: ConflationEngine, uri: str):
    import websockets
    import json
    
    async with websockets.connect(uri) as ws:
        # Subscribe to asset
        await ws.send(json.dumps({"subscribe": symbol}))
        
        async for message in ws:
            data = json.loads(message)
            # Push instantly to the Conflation Engine
            await engine.ingest_tick(symbol, data['tick'])
