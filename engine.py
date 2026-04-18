import asyncio
import random
import time
from typing import Dict, Any

# ==========================================
# CORE: O(1) MEMORY CONFLATION ENGINE
# ==========================================
class ConflationEngine:
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._state_updated = asyncio.Event()

    async def ingest_tick(self, symbol: str, data: Any):
        async with self._lock:
            self._state[symbol] = data 
        self._state_updated.set() 

    async def consume_snapshot(self) -> Dict[str, Any]:
        await self._state_updated.wait() 
        async with self._lock:
            snapshot = self._state.copy()
            self._state.clear()
            self._state_updated.clear()
        return snapshot

# ==========================================
# PARALLEL I/O: NETWORK STREAM SIMULATOR
# ==========================================
async def symbol_stream(symbol: str, engine: ConflationEngine):
    """Simulates a highly aggressive websocket feed for a single symbol."""
    try:
        price = 100.0
        while True:
            # Simulate random market volatility and network tick arrival
            price += random.uniform(-0.1, 0.1)
            await engine.ingest_tick(symbol, {"price": round(price, 3), "timestamp": time.time()})
            
            # Streaming data at 10 to 50 ticks per second (highly volatile)
            await asyncio.sleep(random.uniform(0.02, 0.1))
    except asyncio.CancelledError:
        print(f"[{symbol}] Stream gracefully terminated.")

# ==========================================
# EXECUTION: STRATEGY PROCESSOR
# ==========================================
async def strategy_processor(engine: ConflationEngine):
    """The central brain: scans all updated states and executes logic."""
    try:
        cycles = 0
        while True:
            # Block until at least one new tick arrives, then pull everything
            market_state = await engine.consume_snapshot()
            cycles += 1
            
            # Print state summary every 10 cycles to avoid console spam
            if cycles % 10 == 0:
                print(f"[PROCESSOR] Execution Cycle {cycles} | Processed {len(market_state)} simultaneous symbol updates.")
            
            # Simulate algorithmic math, indicator calculation, and risk checks (50ms latency)
            await asyncio.sleep(0.05) 
            
    except asyncio.CancelledError:
        print("\n[PROCESSOR] Shutting down execution engine...")

# ==========================================
# ORCHESTRATOR: MAIN ENTRY POINT
# ==========================================
async def main():
    print("INITIALIZING PARALLEL SCANNER ARCHITECTURE...")
    engine = ConflationEngine()

    # Define a large array of parallel symbols to scan
    # E.g., scaling up to 92 simultaneous assets
    symbols = [f"VOL_{i}00" for i in range(1, 15)] 
    
    print(f"Booting {len(symbols)} parallel streams...")

    # 1. Spin up the background strategy processor
    processor_task = asyncio.create_task(strategy_processor(engine))

    # 2. Spin up all parallel websocket streams
    stream_tasks = [asyncio.create_task(symbol_stream(sym, engine)) for sym in symbols]

    try:
        # Keep the main loop alive indefinitely while tasks run in the background
        await asyncio.gather(processor_task, *stream_tasks)
    except KeyboardInterrupt:
        # Standardize exit protocol for production
        print("\n[SYSTEM] Intercepted manual kill command. Initiating graceful shutdown...")
        
        # Cancel all background tasks
        processor_task.cancel()
        for task in stream_tasks:
            task.cancel()
            
        # Wait for all tasks to finalize their shutdown routines
        await asyncio.gather(processor_task, *stream_tasks, return_exceptions=True)
        print("[SYSTEM] All streams closed. Memory cleared. Exit successful.")

if __name__ == "__main__":
    try:
        # Run the isolated asyncio event loop
        asyncio.run(main())
    except KeyboardInterrupt:
        pass # Catch the final bubble-up of the interrupt
