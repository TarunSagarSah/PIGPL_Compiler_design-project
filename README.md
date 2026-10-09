# PiGPL — Python-inspired General Purpose Language

**Phase 1 Prototype — VIT Compiler Design Laboratory (Individual Project)**

> Status: this README describes exactly what is implemented in Phase 1. Anything
> not yet built is explicitly labeled **Planned for Phase 2** or **Planned for
> Phase 3** — nothing here is a claim about functionality that doesn't exist yet.

---

## 1. What PiGPL is

PiGPL (**P**ython-**i**nspired **G**eneral **P**urpose **L**anguage) is a small,
custom general-purpose programming language with its own lexical rules, grammar,
and semantic rules. It borrows Python's *readability* — clear keywords, simple
statements — but is **not** Python and is **not** compatible with it. PiGPL is
the subject of a complete, individually-implemented compiler pipeline built for
the Compiler Design Laboratory course.

## 2. Why it exists

Most programming environments hide the compiler's internal work: you write
source code, and you see a final result. The transformations in between —
tokenization, parsing, AST construction, semantic checking, and so on — stay
invisible. PiGPL's defining goal is **observability**: every stage of
compilation is exposed through a visual dashboard, so the relationship between
source code and each intermediate representation can actually be inspected,
not just described.

## 3. Architecture

```
PiGPL Source Code
        |
        v
  Lexical Analyzer  ─────────►  Token Stream
        |
        v
  Parser / Syntax Analyzer ──► Parse Tree / AST
        |
        v
  Semantic Analyzer  <────►  Symbol Table
        |
        v
  Intermediate Code Generator      (Planned — Phase 2)
        |
        v
  Optimizer                        (Planned — Phase 3)
        |
        v
  Target Code Generator            (Planned — Phase 3)
        |
        v
  Execution Engine                 (Planned — Phase 3)
        |
        v
  Final Program Output             (Planned — Phase 3)
```

A separate **Visualization Layer** (`visualization/`) observes the output of
every stage and renders it (tables, tree diagrams, pipeline diagrams) without
altering compiler semantics — it is presentation only, not a compiler phase.

## 4. Language syntax

```pigpl
let x: int = 10

if x > 5 {
    print("Greater")
}
```

### 4.1 Full language specification (target design)

| Category | Keywords / symbols |
|---|---|
| Declarations / types | `let`, `int`, `float`, `bool`, `string` |
| Control flow | `if`, `elif`, `else`, `for`, `while`, `in` |
| Functions | `fn`, `return` |
| I/O | `print`, `input` |
| Boolean literals | `true`, `false` |
| Logical operators | `and`, `or`, `not` |
| Arithmetic | `+ - * / %` |
| Relational | `== != < > <= >=` |
| Assignment | `=` |
| Delimiters | `( ) { } [ ] , :` |
| Comment | `#` to end of line |

The **lexer recognizes this entire keyword set already** (see `compiler/lexer.py`)
so that Phase 2/3 grammar extensions require no lexer changes.

### 4.2 Phase 1 implemented subset

Phase 1 deliberately implements a **small, reliable** part of the language so it
can be demonstrated confidently in a viva:

- Variable declarations: `let name: type = expression`
- Assignment: `name = expression`
- Literals: integer, float, string, boolean (`true`/`false`)
- Arithmetic expressions: `+ - * / %`, unary `-`
- Comparison expressions: `== != < > <= >=`
- `print(expression)`
- `if expression { ... } else { ... }` (no `elif` yet)

**Not yet implemented** (see §11/§12 below): `elif`, `for`, `while`, functions
(`fn`/`return`), lists, `and`/`or`/`not`, `input()`.

## 5. Token categories

| Token category | Examples |
|---|---|
| KEYWORD-derived (`LET`, `IF`, `FN`, ...) | `let`, `if`, `fn`, `return`, `true` |
| `TYPE` | `int`, `float`, `bool`, `string` |
| `IDENTIFIER` | `x`, `total_sum` |
| `INTEGER` | `10`, `42` |
| `FLOATNUM` | `3.14` |
| `STRING` | `"Greater"` |
| Arithmetic operators | `PLUS`, `MINUS`, `TIMES`, `DIVIDE`, `MODULO` |
| Relational operators | `EQ`, `NEQ`, `LT`, `GT`, `LE`, `GE` |
| `ASSIGN` | `=` |
| Delimiters | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `LBRACKET`, `RBRACKET`, `COMMA`, `COLON` |

## 6. Grammar (Phase 1 implemented subset, EBNF-style)

```
program     ::= statement*
statement   ::= declaration | assignment | if_stmt | print_stmt
declaration ::= "let" IDENTIFIER ":" type "=" expression
assignment  ::= IDENTIFIER "=" expression
print_stmt  ::= "print" "(" expression ")"
if_stmt     ::= "if" expression block ("else" block)?
block       ::= "{" statement* "}"
expression  ::= comparison
comparison  ::= term (("=="|"!="|"<"|">"|"<="|">=") term)*
term        ::= factor (("+"|"-") factor)*
factor      ::= unary (("*"|"/"|"%") unary)*
unary       ::= "-" unary | primary
primary     ::= INTEGER | FLOATNUM | STRING | "true" | "false"
              | IDENTIFIER | "(" expression ")"
type        ::= "int" | "float" | "bool" | "string"
```

The full target grammar (with `elif`/`for`/`while`, functions, lists, logical
operators) is documented in the Phase 1 design document and will be added
incrementally in Phase 2 — see §11.

## 7. Compiler phases (project-wide)

| Phase | Concept |
|---|---|
| Lexical analysis | Character stream → classified tokens |
| Syntax analysis | Token stream → parse tree, validated against the grammar |
| AST construction | Parse structure → compact tree for semantic analysis |
| Semantic analysis | Declarations, types, scope |
| Symbol table | Identifier storage and lookup |
| Intermediate code | AST → three-address-code-style IR |
| Optimization | Semantics-preserving IR improvements (e.g. constant folding) |
| Target code generation | Optimized IR → selected target representation |
| Execution | Run the target representation, produce final output |
| Error handling | Phase-tagged diagnostics at every stage |
| Visualization | Stage-by-stage inspection interface |

## 8. Phase 1 implementation

| Module | Responsibility |
|---|---|
| `compiler/lexer.py` | PLY-based lexer; full PiGPL keyword/operator/delimiter set; lexical error reporting |
| `compiler/parser.py` | PLY-based (LALR) parser for the Phase 1 grammar subset; builds the AST |
| `compiler/pigpl_ast.py` | AST node class definitions |
| `compiler/symbol_table.py` | Flat symbol table (name/type/scope/value), scope-stack-ready for Phase 2 |
| `compiler/semantic.py` | Declaration, type, and identifier-declared checks; produces ✓/✗ check list |
| `compiler/errors.py` | Shared `CompilerError` type used by every phase |
| `compiler/ir.py`, `compiler/optimizer.py`, `compiler/codegen.py` | **Architected placeholders** — stable planned interfaces, `NotImplementedError` bodies, clearly labeled Phase 2 / Phase 3 |
| `visualization/token_view.py` | Token table + JSON export |
| `visualization/ast_visualizer.py` | Matplotlib-based AST tree PNG renderer |
| `visualization/symbol_table_view.py` | Symbol table JSON export |
| `visualization/pipeline.py` | Full compiler pipeline diagram (implemented vs. planned stages) |
| `app.py` | Flask app wiring the pipeline to the dashboard UI |
| `ui/` | Dashboard HTML/CSS/JS (source editor, stage rail, output panel) |

## 9. Installation (Windows, or any OS with Python 3.10+)

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt
```

No system-level Graphviz install is required — AST and pipeline diagrams are
rendered with `matplotlib`, which installs with a single `pip install`.

## 10. Running the project

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in a browser. Write or load an example
PiGPL program, click **Compile & Analyze**, and click through the stage rail
on the left (Source, Lexical Analysis, Tokens, Syntax Analysis, AST, Symbol
Table, Semantic Analysis, planned stages, Errors, Full Pipeline Diagram).

### 10.1 Example programs (`examples/`)

| File | Demonstrates |
|---|---|
| `basic.pig` | A single declaration and `print` |
| `arithmetic.pig` | Operator precedence (`+ - * /`) |
| `if_example.pig` | `if` / `else` with a comparison condition |
| `lexical_error.pig` | Invalid character (`@`) |
| `syntax_error.pig` | Incomplete declaration (missing expression) |
| `semantic_error.pig` | Undeclared identifier used in an expression |

### 10.2 Expected outputs

For a valid program, the dashboard shows: the token table, a green "no
syntax errors" message, a rendered AST tree image, a populated symbol table,
and a list of ✓ semantic checks. Generated artifacts are also written to disk
under `outputs/` (`outputs/ast/ast.png`, `outputs/tokens/tokens.json`,
`outputs/symbol_table/symbol_table.json`, `outputs/diagrams/compiler_pipeline.png`)
so they can be shown even outside the browser during a review.

For an invalid program, the relevant phase's tab (Lexical Analysis / Syntax
Analysis / Semantic Analysis) and the consolidated **Errors** tab show a card
per diagnostic: phase, message, line, column.

## 11. Known limitations (Phase 1)

- Grammar subset only: no `elif`, `for`, `while`, functions, lists, or logical
  `and`/`or`/`not` yet (all are tokenized already; only the parser doesn't
  build them into statements/expressions yet).
- Semantic analysis has a single (`global`) scope; no function-based scoping.
- No intermediate code, optimization, target code, or execution — these are
  architected as placeholder modules (`compiler/ir.py`, `compiler/optimizer.py`,
  `compiler/codegen.py`) that raise `NotImplementedError` and are clearly
  labeled "Planned" in both the code and the dashboard.
- Parser error recovery is minimal: parsing stops at the first syntax error
  rather than attempting multi-error recovery.

## 12. Phase 2 plan

- Extend the grammar: `elif`, `for`, `while`/`in`, function definitions
  (`fn`/`return`), function calls, lists/arrays, logical `and`/`or`/`not`.
- Add real lexical-scope support to `SymbolTable` (its `enter_scope`/`exit_scope`
  methods already exist for this).
- Extend semantic analysis: function signatures, parameter/return-type
  checking, scope-aware declaration checks.
- Implement `compiler/ir.py`: translate the AST into three-address-code-style
  instructions, and add an IR view to the dashboard.

## 13. Phase 3 plan

- Implement `compiler/optimizer.py`: constant folding and other safe, local,
  semantics-preserving optimizations, with a before/after IR view.
- Implement `compiler/codegen.py`: target-level code generation (the exact
  target — assembly-like code, bytecode, or another representation — will be
  finalized based on implementation effort and educational value, per the
  Phase 1 design document).
- Implement execution of the generated target representation and display the
  final program output in the dashboard.
- Broaden testing: valid, invalid, boundary, and complex-input test cases;
  richer error recovery.

## 14. Phase 1 Requirement Coverage

| Requirement | Implementation |
|---|---|
| Problem Definition | `PiGPL_Phase_1_Problem_Definition_and_System_Design.pdf` (project document) |
| Language Specification | §4–§6 above; `compiler/lexer.py`, `compiler/parser.py` |
| Prototype | This working Flask web application |
| Lexical Analysis | `compiler/lexer.py` |
| Syntax Analysis | `compiler/parser.py` |
| AST | `compiler/pigpl_ast.py` |
| Symbol Table | `compiler/symbol_table.py` |
| Semantic Analysis | `compiler/semantic.py` |
| Visualization | `visualization/` |
| Error Handling | `compiler/errors.py`, surfaced across all phases |
| Intermediate Code (planned) | `compiler/ir.py` |
| Optimization (planned) | `compiler/optimizer.py` |
| Target Code / Execution (planned) | `compiler/codegen.py` |

## 15. Project structure

```
PiGPL/
├── app.py
├── README.md
├── requirements.txt
├── compiler/
│   ├── __init__.py
│   ├── lexer.py
│   ├── parser.py
│   ├── pigpl_ast.py
│   ├── symbol_table.py
│   ├── semantic.py
│   ├── errors.py
│   ├── ir.py            
│   ├── optimizer.py    
│   └── codegen.py       
├── visualization/
│   ├── __init__.py
│   ├── token_view.py
│   ├── ast_visualizer.py
│   ├── symbol_table_view.py
│   └── pipeline.py
├── ui/
│   ├── templates/index.html
│   └── static/{style.css, script.js}
├── examples/
│   ├── basic.pig
│   ├── arithmetic.pig
│   ├── if_example.pig
│   ├── lexical_error.pig
│   ├── syntax_error.pig
│   └── semantic_error.pig
└── outputs/
    ├── ast/            (ast.png)
    ├── tokens/         (tokens.json)
    ├── symbol_table/   (symbol_table.json)
    ├── diagrams/       (compiler_pipeline.png)
    └── reports/
```

## 16. Demonstrating this to a teacher

1. Run `python app.py`, open the dashboard.
2. Load `examples/if_example.pig`, click **Compile & Analyze** — walk through
   Tokens → AST (point at the rendered tree image) → Symbol Table → Semantic
   Analysis (✓ checklist).
3. Load `examples/lexical_error.pig`, `syntax_error.pig`, and
   `semantic_error.pig` one at a time to show phase-tagged error reporting in
   the **Errors** tab.
4. Open the **Full Pipeline Diagram** tab to show the complete architecture,
   with Phase 1 stages in green and Phase 2/3 stages clearly marked "Planned".
5. Open `outputs/` in a file browser to show the exportable artifacts
   (`ast.png`, `tokens.json`, `symbol_table.json`, `compiler_pipeline.png`)
   generated by the run.

## 17. References

[1] A. V. Aho, M. S. Lam, R. Sethi, and J. D. Ullman, *Compilers: Principles,
Techniques, and Tools*, 2nd ed., Pearson, 2006.
[2] K. D. Cooper and L. Torczon, *Engineering a Compiler*, 2nd ed., Morgan
Kaufmann, 2011.
[3] A. W. Appel, *Modern Compiler Implementation in Java*, 2nd ed., Cambridge
University Press, 2002.
