import time
import threading
import lodestone

# --- Configuration Settings ---
SERVER_IP = "minenigger.tkmc.net"          # Server address
SERVER_PORT = 25565                       # Default Minecraft port
BOT_USERNAME = "rwlitafk"                  # Custom bot username
MINECRAFT_VERSION = "1.21.1"              # Network protocol covering 1.21.11

def jump_every_5_minutes(bot_instance, stop_event):
    """Background thread that triggers an anti-AFK jump exactly every 5 minutes."""
    while not stop_event.is_set():
        for _ in range(300): # 300 seconds = 5 minutes
            if stop_event.is_set():
                return
            time.sleep(1)
            
        try:
            if bot_instance.bot and bot_instance.bot.entity:
                print("🦘 5 minutes passed: Executing anti-AFK jump...")
                bot_instance.setControlState('jump', True)
                time.sleep(0.3)
                bot_instance.setControlState('jump', False)
                bot_instance.swingArm('right')
        except Exception:
            break

def server_connection_heartbeat(bot_instance, stop_event):
    """
    Independent monitor thread. Checks every 30 seconds if the bot 
    is actively connected to the server. If it handles a ghost/silent 
    disconnect, it triggers a clean reconnection.
    """
    while not stop_event.is_set():
        time.sleep(30)
        if stop_event.is_set():
            return
            
        is_alive = False
        try:
            if bot_instance.bot and bot_instance.bot.entity and bot_instance.bot.isLoggedIn:
                is_alive = True
        except Exception:
            is_alive = False

        if not is_alive:
            print("⚠️ [Heartbeat Monitor]: Bot silent/ghost disconnect detected!")
            try:
                bot_instance.bot.end() # Force close dead socket safely
            except Exception:
                pass
            break 

def create_afk_bot():
    print(f"🚀 Connecting 24/7 AFK client to {SERVER_IP} as {BOT_USERNAME}...")
    
    stop_threads = threading.Event()

    try:
        bot = lodestone.createBot(
            host=SERVER_IP,
            port=SERVER_PORT,
            username=BOT_USERNAME,
            auth='offline',              # Force cracked/offline mode
            version=MINECRAFT_VERSION
        )
    except Exception as e:
        print(f"❌ Failed to initialize bot connection: {e}")
        handle_reconnect(stop_threads)
        return

    # 1. Spawn behavior and automatic modules
    @bot.on('spawn')
    def handle_spawn(*args):
        print(f"🤖 {BOT_USERNAME} spawned into the server successfully!")
        time.sleep(2) # Wait 2 seconds for server stability
        
        # Request all-black skin appearance if SkinRestorer is on the network
        bot.chat("/skin PitchBlack") 
        print("👕 Sent black skin appearance cosmetic request.")
        
        # Start the background checking and jumping modules
        threading.Thread(target=jump_every_5_minutes, args=(bot, stop_threads), daemon=True).start()
        threading.Thread(target=server_connection_heartbeat, args=(bot, stop_threads), daemon=True).start()
        print("⏱️ Anti-AFK jumper (5m) and Active Status Connection monitor started.")

    # 2. Clean Auto-Reconnect Loop 
    @bot.on('end')
    def handle_disconnect(reason, *args):
        print(f"❌ Bot disconnected from server. Reason: {reason}")
        handle_reconnect(stop_threads)

def handle_reconnect(stop_event):
    """Signals all monitoring threads to stop and starts a countdown loop to reconnect."""
    if not stop_event.is_set():
        stop_event.set() 
        print("⏳ Attempting automatic reconnection in 20 seconds...")
        time.sleep(20)
        create_afk_bot() 

if __name__ == "__main__":
    create_afk_bot()
