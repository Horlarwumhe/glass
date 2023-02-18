import argparse
import os
import sys

usage = """

Glass cli

Options:
	--help Show this help message

Commands:

 routes   Show routes for the app
 run      Run the app developemnt server
 config   Show the app configurations

run
=======

glass run

Start the app development server

Options:
    --host server host [default: localhost]
    --port server port [default: 8000]
"""


RUN_DEBUG = """Starting Glass development server on port {host}:{port}
"""


def find_path(path):
    """Given a filename this will try to calculate the python path, add it
    to the search path and return the actual module name that is expected.
    """
    path = os.path.realpath(path)

    fname, ext = os.path.splitext(path)
    if ext == ".py":
        path = fname

    if os.path.basename(path) == "__init__":
        path = os.path.dirname(path)

    module_name = []

    # move up until outside package structure (no __init__.py)
    while True:
        path, name = os.path.split(path)
        module_name.append(name)

        if not os.path.exists(os.path.join(path, "__init__.py")):
            break

    if sys.path[0] != path:
        sys.path.insert(0, path)

    return ".".join(module_name[::-1])


def find_app(module_name):
    # __traceback_hide__ = True  # noqa: F841
    os.environ["GLASS_FROM_CLI"] = "true"
    module_name = find_path(module_name)
    __import__(module_name)

    module = sys.modules[module_name]
    return getattr(module, "app")


def run_app(arg):

    app = find_app(arg.app)
    del os.environ["GLASS_FROM_CLI"]
    print(RUN_DEBUG.format(host=arg.host, port=arg.port))
    app.run(host=arg.host, port=arg.port, debug=True)


def show_routes(arg):
    head = []
    rules = []
    methods = []
    callbacks = []

    app = find_app(arg.app)
    routes = app.url_rules
    max_rule_len = max_func_len = max_method_len = 1
    for route in routes:
        rules.append(route.url_rule)
        method = ",".join(route.methods)
        methods.append(method)
        callbacks.append(route.callback.__name__)

        if len(route.url_rule) > max_rule_len:
            max_rule_len = len(route.url_rule)
        if len(methods) > max_method_len:
            max_method_len = len(method)
        if len(route.callback.__name__) > max_func_len:
            max_func_len = len(route.callback.__name__)

    print(
        "\tRules",
        " " * (max_rule_len - 3),
        "Callback",
        " " * (max_func_len - 5),
        "Methods",
        sep="",
    )
    print("\t", "-" * max_rule_len, "-" * max_func_len, "---------")
    lines = []
    for rule, callback, method in zip(rules, callbacks, methods):
        line = ["\t"]
        line.append(rule)
        line.append(" " * (max_rule_len - len(rule) + 2))
        line.append(callback + " " * (max_func_len - len(callback) + 2))
        line.append(method + "\n")
        lines.append("".join(line))

    print("".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Glass cli", usage=usage)
    parser.add_argument("cmd")
    parser.add_argument("--app", default="app.py")
    parser.add_argument("--port", default=8000)
    parser.add_argument("--host", default="localhost")
    p = parser.parse_args()
    # import pdb
    # pdb.set_trace()
    if p.cmd == "routes":
        show_routes(p)
    elif p.cmd == "run":
        run_app(p)


if __name__ == "__main__":
    main()
