import sys


def main():
    """Run the MacroSignage development server."""
    from macrosignage import macro_signage_app

    host = "127.0.0.1"
    port = 5000
    debug = False

    for arg in sys.argv[1:]:
        if arg.startswith("--host="):
            host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])
        elif arg == "--debug":
            debug = True

    app = macro_signage_app()
    app.run(host=host, port=port, debug=debug)
