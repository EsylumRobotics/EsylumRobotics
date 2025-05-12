import subprocess
import time
import webbrowser

# Path to your server file
server_script = "C:/Path/To/Your/Server/conclave_server.py"  # <<< UPDATE THIS

# Start the Flask server
subprocess.Popen(["python", server_script])

# Wait a few seconds for server to start
time.sleep(3)

# Open Conclave Dashboard in browser (optional)
webbrowser.open("http://127.0.0.1:5000")

print("🚀 Conclave launched successfully!")
