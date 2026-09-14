import signal
import asyncio
import importlib
import os
import uvicorn

from anony import app, db, logger
from anony.modules import all_modules
from anony.web_server import app_web  # Ensure this is implemented as discussed

async def idle():
    """Keep the bot running and handle shutdown signals."""
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
    except NotImplementedError:
        # Fallback for systems where add_signal_handler is not available (e.g., Windows)
        def handler(sig, frame):
            loop.call_soon_threadsafe(stop_event.set)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    await stop_event.wait()

async def anony_boot():
    """Unified startup for Bot and FastAPI Web Server."""
    try:
        # 1. Start Bot Client
        await app._start()
    except Exception as ex:
        raise RuntimeError(ex)
    
    # 2. Connect to Database
    await db.connect()

    # 3. Load Bot Modules
    imported = [
        importlib.import_module(f"anony.modules.{module}")
        for module in all_modules()
    ]
    logger.info(f"Loaded {len(imported)} modules.")

    # 4. Configure Web Server (FastAPI)
    port = int(os.environ.get("PORT", 8080))
    config = uvicorn.Config(
        app_web, 
        host="0.0.0.0", 
        port=port, 
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)

    # 5. Run both services concurrently
    logger.info(f"Starting Web Server on port {port}...")
    
    # We use gather to run the uvicorn server and the bot's idle listener simultaneously
    # If either fails or receives a stop signal, we proceed to shutdown
    try:
        await asyncio.gather(
            server.serve(),
            idle()
        )
    finally:
        # 6. Graceful Shutdown
        logger.info("Initiating shutdown...")
        await app._stop()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(anony_boot())
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.error(f"Critical error: {ex}")
    finally:
        logger.info("Service stopped.")
        
