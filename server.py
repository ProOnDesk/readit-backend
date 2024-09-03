import uvicorn
import sys

if __name__ == "__main__":
    args = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": True
    }

    if "https" in sys.argv:
        args.update({
            "ssl_keyfile": "app/key.pem",
            "ssl_certfile": "app/cert.pem"
        })

    uvicorn.run(**args)