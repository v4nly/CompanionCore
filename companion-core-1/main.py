import threading
import webview
from app import app

def iniciar_flask():
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)

if __name__ == "__main__":
    t = threading.Thread(target=iniciar_flask)
    t.daemon = True
    t.start()

    webview.create_window(
        title="Companion AI - Aoi", 
        url="http://127.0.0.1:8000", 
        width=600, 
        height=700,
        resizable=True,
        background_color="#121212"
    )
    webview.start()