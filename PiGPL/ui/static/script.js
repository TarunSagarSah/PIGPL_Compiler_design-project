/* =========================================================================
   PiGPL Dashboard client logic
   -------------------------------------------------------------------------
   Responsibilities:
     1. Load example .pig programs into the source picker.
     2. POST the current source to /api/compile and store the JSON result.
     3. Render whichever stage is currently selected in the stage rail.
     4. Keep the "Errors" tab's badge count and the rail's active state in
        sync with the latest compile result.
   ========================================================================= */

const state = {
  lastResult: null,
  activeStage: "source",
};

const els = {
  sourceInput: document.getElementById("source-input"),
  examplePicker: document.getElementById("example-picker"),
  compileBtn: document.getElementById("compile-btn"),
  statusLine: document.getElementById("status-line"),
  stageList: document.getElementById("stage-list"),
  outputTitle: document.getElementById("output-title"),
  outputBody: document.getElementById("output-body"),
  errorCount: document.getElementById("error-count"),
};

const STAGE_TITLES = {
  source: "Source",
  lexical: "Lexical Analysis",
  tokens: "Token Stream",
  syntax: "Syntax Analysis",
  ast: "Parse Tree / AST",
  symbols: "Symbol Table",
  semantic: "Semantic Analysis",
  ir: "Intermediate Code",
  optimize: "Optimization",
  target: "Target Code",
  execution: "Execution",
  errors: "Errors",
  pipeline: "Full Pipeline Diagram",
};

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

/* ------------------------------------------------------------- examples */
async function loadExampleList() {
  try {
    const res = await fetch("/api/examples");
    const names = await res.json();
    for (const name of names) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      els.examplePicker.appendChild(opt);
    }
  } catch (e) {
    // Non-fatal: the picker just stays empty if examples can't be listed.
  }
}

els.examplePicker.addEventListener("change", async () => {
  const name = els.examplePicker.value;
  if (!name) return;
  const res = await fetch(`/api/examples/${encodeURIComponent(name)}`);
  const data = await res.json();
  if (data.source !== undefined) {
    els.sourceInput.value = data.source;
  }
});

/* ------------------------------------------------------------- compile */
els.compileBtn.addEventListener("click", compile);

async function compile() {
  els.compileBtn.disabled = true;
  els.statusLine.textContent = "Compiling…";
  els.statusLine.className = "status-line";
  try {
    const res = await fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: els.sourceInput.value }),
    });
    const data = await res.json();
    state.lastResult = data;

    const errCount = data.all_errors ? data.all_errors.length : 0;
    if (errCount > 0) {
      els.statusLine.textContent = `Compiled with ${errCount} error(s).`;
      els.statusLine.className = "status-line err";
    } else {
      els.statusLine.textContent = "Compiled successfully — no errors.";
      els.statusLine.className = "status-line ok";
    }

    updateErrorBadge(errCount);
    renderStage(state.activeStage);
  } catch (e) {
    els.statusLine.textContent = "Request failed: " + e;
    els.statusLine.className = "status-line err";
  } finally {
    els.compileBtn.disabled = false;
  }
}

function updateErrorBadge(count) {
  if (count > 0) {
    els.errorCount.hidden = false;
    els.errorCount.textContent = String(count);
  } else {
    els.errorCount.hidden = true;
  }
}

/* ------------------------------------------------------------- stage nav */
els.stageList.addEventListener("click", (e) => {
  const li = e.target.closest("li[data-stage]");
  if (!li) return;
  state.activeStage = li.dataset.stage;
  [...els.stageList.children].forEach((c) => c.classList.remove("active"));
  li.classList.add("active");
  renderStage(state.activeStage);
});

// Mark "Source" active by default.
els.stageList.querySelector('[data-stage="source"]').classList.add("active");

/* ------------------------------------------------------------- rendering */
function renderStage(stage) {
  els.outputTitle.textContent = STAGE_TITLES[stage] || stage;
  const r = state.lastResult;

  if (stage === "source") {
    els.outputBody.innerHTML = `<div class="code-block">${escapeHtml(els.sourceInput.value)}</div>`;
    return;
  }

  if (!r) {
    els.outputBody.innerHTML = emptyState();
    return;
  }

  switch (stage) {
    case "lexical":
      renderLexical(r);
      break;
    case "tokens":
      renderTokens(r);
      break;
    case "syntax":
      renderSyntax(r);
      break;
    case "ast":
      renderAst(r);
      break;
    case "symbols":
      renderSymbols(r);
      break;
    case "semantic":
      renderSemantic(r);
      break;
    case "ir":
      renderPlanned("Intermediate Code Generation", "compiler/ir.py",
        "Will translate the AST into three-address-code-style instructions once implemented in Phase 2.");
      break;
    case "optimize":
      renderPlanned("Optimization", "compiler/optimizer.py",
        "Will apply constant folding and similar safe, semantics-preserving transformations to the IR once implemented in Phase 3.");
      break;
    case "target":
      renderPlanned("Target Code Generation", "compiler/codegen.py",
        "Will translate optimized IR into a selected target-level representation once implemented in Phase 3.");
      break;
    case "execution":
      renderPlanned("Execution", "compiler/codegen.py",
        "Will run the target representation and display the final program output once implemented in Phase 3.");
      break;
    case "errors":
      renderErrors(r);
      break;
    case "pipeline":
      renderPipeline(r);
      break;
    default:
      els.outputBody.innerHTML = emptyState();
  }
}

function emptyState() {
  return `<div class="empty-state">
    <p>Click <strong>Compile &amp; Analyze</strong> to run this stage.</p>
  </div>`;
}

function renderLexical(r) {
  const errs = r.lexical_errors || [];
  let html = "";
  if (errs.length === 0) {
    html += `<div class="no-errors">No lexical errors — every character formed a valid PiGPL token.</div>`;
  } else {
    html += errorCards(errs);
  }
  html += `<p style="color:var(--muted); font-size:13px; margin-top:14px;">${r.tokens.length} token(s) recognized. See the <strong>Tokens</strong> tab for the full stream.</p>`;
  els.outputBody.innerHTML = html;
}

function renderTokens(r) {
  if (!r.tokens || r.tokens.length === 0) {
    els.outputBody.innerHTML = `<div class="empty-state"><p>No tokens produced.</p></div>`;
    return;
  }
  let rows = r.tokens.map(t => `
    <tr>
      <td>${escapeHtml(t.lexeme)}</td>
      <td><span class="badge">${escapeHtml(t.type)}</span></td>
      <td>${t.line}</td>
      <td>${t.column}</td>
    </tr>`).join("");
  els.outputBody.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Lexeme</th><th>Token Type</th><th>Line</th><th>Column</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderSyntax(r) {
  const errs = r.syntax_errors || [];
  if (errs.length === 0) {
    els.outputBody.innerHTML = `<div class="no-errors">No syntax errors — the token stream matches the PiGPL grammar.</div>
      <p style="color:var(--muted); font-size:13px; margin-top:14px;">See the <strong>AST</strong> tab for the resulting parse tree.</p>`;
  } else {
    els.outputBody.innerHTML = errorCards(errs);
  }
}

function renderAst(r) {
  if (r.ast_image) {
    els.outputBody.innerHTML = `<img class="stage-image" src="${r.ast_image}?t=${Date.now()}" alt="AST diagram">
      <p style="color:var(--muted); font-size:12.5px; margin-top:10px;">Saved to <code style="color:var(--accent)">outputs/ast/ast.png</code></p>`;
  } else {
    els.outputBody.innerHTML = `<div class="empty-state"><p>No AST available — fix syntax errors first.</p></div>`;
  }
}

function renderSymbols(r) {
  const rows = r.symbol_table || [];
  if (rows.length === 0) {
    els.outputBody.innerHTML = `<div class="empty-state"><p>No symbols recorded yet.</p></div>`;
    return;
  }
  const body = rows.map(s => `
    <tr>
      <td>${escapeHtml(s.name)}</td>
      <td><span class="badge">${escapeHtml(s.type)}</span></td>
      <td>${escapeHtml(s.scope)}</td>
      <td>${s.value === null || s.value === undefined ? "—" : escapeHtml(s.value)}</td>
    </tr>`).join("");
  els.outputBody.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Name</th><th>Type</th><th>Scope</th><th>Value / Attribute</th></tr></thead>
      <tbody>${body}</tbody>
    </table>`;
}

function renderSemantic(r) {
  const checks = r.semantic_checks || [];
  const errs = r.semantic_errors || [];
  let html = "";
  if (checks.length === 0 && errs.length === 0) {
    html = `<div class="empty-state"><p>Semantic analysis has not run yet (it requires a syntax-error-free program).</p></div>`;
  } else {
    const items = checks.map(c => {
      const pass = c.startsWith("\u2713");
      return `<li class="${pass ? "pass" : "fail"}">${escapeHtml(c)}</li>`;
    }).join("");
    html = `<ul class="check-list">${items}</ul>`;
    if (errs.length) {
      html += `<div style="margin-top:16px;">${errorCards(errs)}</div>`;
    }
  }
  els.outputBody.innerHTML = html;
}

function renderPlanned(title, module, description) {
  els.outputBody.innerHTML = `
    <div class="planned-note">
      <strong style="color:var(--text)">${escapeHtml(title)} — Planned for a later phase.</strong><br><br>
      ${escapeHtml(description)}<br><br>
      Architected in <code>${escapeHtml(module)}</code> with a stable interface; not implemented in Phase 1
      so this stage is not misrepresented as working.
    </div>`;
}

function renderErrors(r) {
  const errs = r.all_errors || [];
  if (errs.length === 0) {
    els.outputBody.innerHTML = `<div class="no-errors">No errors across any phase. This program is valid PiGPL (Phase 1 subset).</div>`;
  } else {
    els.outputBody.innerHTML = errorCards(errs);
  }
}

function renderPipeline(r) {
  if (r.pipeline_image) {
    els.outputBody.innerHTML = `<img class="stage-image" src="${r.pipeline_image}?t=${Date.now()}" alt="Compiler pipeline diagram">
      <p style="color:var(--muted); font-size:12.5px; margin-top:10px;">Saved to <code style="color:var(--accent)">outputs/diagrams/compiler_pipeline.png</code></p>`;
  } else {
    els.outputBody.innerHTML = emptyState();
  }
}

function errorCards(errs) {
  return errs.map(e => `
    <div class="error-card">
      <div class="phase-line">${escapeHtml(e.phase)} Error</div>
      <div class="msg">${escapeHtml(e.message)}</div>
      <div class="loc">Line ${e.line || "?"} &middot; Column ${e.column || "?"}</div>
    </div>`).join("");
}

/* ------------------------------------------------------------- init */
loadExampleList();
