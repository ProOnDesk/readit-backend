import uvicorn
import sys
import re

if __name__ == "__main__":
    
    args = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": False,
        "reload_excludes": ["app/alembic/*", "app/alembic/versions/*.py"]
    }

    if "--https" in sys.argv:
        args.update({
            "ssl_keyfile": "app/key.pem",
            "ssl_certfile": "app/cert.pem"
        })

    if "--dev" in sys.argv:
        args.update({
            "reload": True,
        })

    if "--host" in sys.argv:
        try:
            host = sys.argv[sys.argv.index("--host") + 1]
        except:
            print("Argument --host requires ip (ex. '--host 0.0.0.0')")

        def is_valid_ip(ip):
            pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if re.match(pattern, ip):
                octets = ip.split('.')
                return all(0 <= int(octet) <= 255 for octet in octets)
            return False

        if not is_valid_ip(host):
            print("Invalid host")
            exit(1)

        args.update({
            "host": host
        })

    if "--port" in sys.argv:
        try:
            port = sys.argv[sys.argv.index("--port") + 1]
        except:
            print("Argument --port requires port (ex. '--port 80')")

        def is_valid_port(port):
            if port >= 0 and port <= 65535: return True
            return False

        if not is_valid_ip(int(port)):
            print("Invalid port")
            exit(1)

        args.update({
            "port": int(port) 
        })

    uvicorn.run(**args)