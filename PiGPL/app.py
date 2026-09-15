"""
app.py
======
Purpose:
    The Flask web application that serves the PiGPL Phase 1 dashboard.
    Wires together the compiler front-end (lexer -> parser -> semantic
    analyzer) and the visualization layer, and exposes them through a
    single-page UI with stage tabs, as required by the Phase 1 design.

Routes:
    GET  /                -> the dashboard (source editor + stage tabs)
    POST /api/compile     -> runs the full Phase 1 pipeline over the
                              submitted source and returns a JSON payload
                              containing every stage's output plus errors
    GET  /outputs/<path>  -> serves generated artifact files (ast.png,
                              compiler_pipeline.png, tokens.json, ...)

Run:
    python app.py
    then open http://127.0.0.1:5000 in a browser.
"""

import os
import traceback

from flask import Flask, jsonify, render_template, request, send_from_directory

from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.semantic import analyze as semantic_analyze
from visualization.ast_visualizer import render_ast
from visualization.pipeline import render_pipeline
from visualization.token_view import tokens_to_table, save_tokens_json
from visualization.symbol_table_view import symbol_table_to_rows, save_symbol_table_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")

app = Flask(__name__, template_folder="ui/templates", static_folder="ui/static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/outputs/<path:filename>")
def outputs(filename):
    return send_from_directory(OUTPUTS_DIR, filename)


@app.route("/api/examples")
def api_examples():
    """List the .pig example files bundled with the project."""
    if not os.path.isdir(EXAMPLES_DIR):
        return jsonify([])
    names = sorted(f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".pig"))
    return jsonify(names)


@app.route("/api/examples/<name>")
def api_example_file(name):
    path = os.path.join(EXAMPLES_DIR, name)
    if not os.path.abspath(path).startswith(os.path.abspath(EXAMPLES_DIR)) or not os.path.isfile(path):
        return jsonify({"error": "not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        return jsonify({"source": f.read()})


@app.route("/api/compile", methods=["POST"])
def api_compile():
    source = request.get_json(force=True).get("source", "")

    result = {
        "source": source,
        "tokens": [],
        "lexical_errors": [],
        "ast": None,
        "ast_image": None,
        "syntax_errors": [],
        "symbol_table": [],
        "semantic_checks": [],
        "semantic_errors": [],
        "pipeline_image": None,
        "all_errors": [],
    }

    try:
        # ---- Stage 1 & 2: Lexical Analysis -> Token Stream --------------
        tokens, lex_errors = tokenize(source)
        result["tokens"] = tokens_to_table(tokens)
        result["lexical_errors"] = [e.to_dict() for e in lex_errors]
        save_tokens_json(tokens, output_dir=os.path.join(OUTPUTS_DIR, "tokens"))

        # ---- Stage 3 & 4: Syntax Analysis -> AST -------------------------
        ast_root, syntax_errors = parse(source)
        result["syntax_errors"] = [e.to_dict() for e in syntax_errors]

        if ast_root is not None:
            result["ast"] = ast_root.to_dict()
            ast_path = render_ast(ast_root, output_path=os.path.join(OUTPUTS_DIR, "ast", "ast.png"))
            result["ast_image"] = "/outputs/" + os.path.relpath(ast_path, OUTPUTS_DIR).replace(os.sep, "/")

        # ---- Stage 5 & 6: Symbol Table + Semantic Analysis ---------------
        # Only run semantic analysis if the program at least parsed, since
        # semantic checks assume a structurally valid AST.
        if ast_root is not None and not syntax_errors:
            symbol_table, checks, sem_errors = semantic_analyze(ast_root)
            result["symbol_table"] = symbol_table_to_rows(symbol_table)
            result["semantic_checks"] = checks
            result["semantic_errors"] = [e.to_dict() for e in sem_errors]
            save_symbol_table_json(symbol_table, output_dir=os.path.join(OUTPUTS_DIR, "symbol_table"))

        # ---- Pipeline diagram (static per compile, always regenerated) --
        pipeline_path = render_pipeline(output_path=os.path.join(OUTPUTS_DIR, "diagrams", "compiler_pipeline.png"))
        result["pipeline_image"] = "/outputs/" + os.path.relpath(pipeline_path, OUTPUTS_DIR).replace(os.sep, "/")

        # ---- Consolidated error list for the "Errors" tab -----------------
        result["all_errors"] = (
            result["lexical_errors"] + result["syntax_errors"] + result["semantic_errors"]
        )

    except Exception as exc:  # pragma: no cover - defensive guard for the live demo
        result["all_errors"].append(
            {"phase": "Internal", "message": f"{exc}", "line": 0, "column": 0}
        )
        traceback.print_exc()

    return jsonify(result)


if __name__ == "__main__":
    os.makedirs(os.path.join(OUTPUTS_DIR, "ast"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUTS_DIR, "tokens"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUTS_DIR, "symbol_table"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUTS_DIR, "diagrams"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUTS_DIR, "reports"), exist_ok=True)
    # use_reloader=False: the reloader's file watcher would otherwise pick
    # up every generated file under outputs/ (tokens.json, ast.png, ...)
    # and keep restarting the server mid-compile.
    app.run(debug=True, port=5000, use_reloader=False)
