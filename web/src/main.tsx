import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Viewer } from "./Viewer";
import {
  formatValue,
  nextRecord,
  symbols,
  visibleRecords,
  valueRows,
} from "./semantics";
import type { Mode, Report } from "./types";
import "./style.css";

function App({ report }: { report: Report }) {
  const records = report.diff.records;
  const [selected, setSelected] = useState(
    records.find((r) => r.changes.some((c) => c.category === "moved"))?.id ||
      records[0]?.id ||
      "",
  );
  const [mode, setMode] = useState<Mode>("Overlay"),
    [mix, setMix] = useState(0.5),
    [changed, setChanged] = useState(false),
    [category, setCategory] = useState("all"),
    [query, setQuery] = useState(""),
    [fit, setFit] = useState(0),
    [reset, setReset] = useState(0);
  const filtered = visibleRecords(records, changed, category, query);
  const navigation = filtered.filter((r) => r.status !== "unchanged");
  const record = records.find((r) => r.id === selected);
  const move = (direction: number) => {
    const id = nextRecord(navigation, selected, direction);
    if (id) setSelected(id);
  };
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).matches("input,select,textarea")) return;
      if (e.key === "]") {
        e.preventDefault();
        move(1);
      }
      if (e.key === "[") {
        e.preventDefault();
        move(-1);
      }
      if (e.key.toLowerCase() === "f") setFit((v) => v + 1);
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  });
  const selectedEntity =
    report.after.entities.find((e) => e.id === record?.after) ||
    report.before.entities.find((e) => e.id === record?.before);
  const sourceEntities = record?.after
    ? report.after.entities
    : report.before.entities;
  const candidates = report.diff.ambiguity.filter(
    (c) => c.before === record?.before || c.after === record?.after,
  );
  return (
    <div className="app">
      <header>
        <div className="brand">
          <span className="brandmark">◈</span>
          <div>
            SEMANTIC CHANGE EXPLORER<small>LOCAL COMPARISON · v0.1.0</small>
          </div>
        </div>
        <div className="sources">
          <span>A</span> {report.before.source.name} <b>→</b> <span>B</span>{" "}
          {report.after.source.name}
        </div>
        <div className="local">● LOCAL FILES</div>
      </header>
      <div className="summary">
        <strong>Understand the difference.</strong>
        <div>
          {Object.entries(report.diff.summary).map(([s, n]) => (
            <span key={s} className={s}>
              {symbols[s]} {n} {s}
            </span>
          ))}
        </div>
      </div>
      <main>
        <aside className="index">
          <div className="section-title">
            CHANGE INDEX <span>{filtered.length} entities</span>
          </div>
          <input
            aria-label="Find entity"
            placeholder="Find an entity…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="filters">
            <label>
              <input
                type="checkbox"
                checked={changed}
                onChange={(e) => setChanged(e.target.checked)}
              />{" "}
              Changed only
            </label>
            <select
              aria-label="Change category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="all">All categories</option>
              {[
                "added",
                "removed",
                "ambiguous",
                "moved",
                "geometry",
                "topology",
                "modifier",
                "material",
                "relationship",
                "evaluated",
              ].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          <nav aria-label="Entities">
            {filtered.map((r) => (
              <button
                key={r.id}
                aria-pressed={selected === r.id}
                onClick={() => setSelected(r.id)}
                className={"entity " + (selected === r.id ? "selected" : "")}
              >
                <span className={"symbol " + r.status}>
                  {symbols[r.status]}
                </span>
                <span>
                  <strong>{r.name}</strong>
                  <small>
                    {r.type.replace("blender.", "")} · {r.status}
                  </small>
                </span>
              </button>
            ))}
            {!filtered.length && (
              <p className="empty">No entities match these filters.</p>
            )}
          </nav>
          <div className="navigation">
            <button onClick={() => move(-1)} disabled={!navigation.length}>
              ← Previous [
            </button>
            <button onClick={() => move(1)} disabled={!navigation.length}>
              Next ] →
            </button>
          </div>
        </aside>
        <section className="spatial">
          <div className="toolbar">
            <div className="modes">
              {(["A", "B", "Overlay", "Compare"] as Mode[]).map((m) => (
                <button
                  key={m}
                  aria-pressed={mode === m}
                  onClick={() => setMode(m)}
                >
                  {m === "A" ? "A only" : m === "B" ? "B only" : m}
                </button>
              ))}
            </div>
            <div>
              <button onClick={() => setFit((v) => v + 1)}>
                Fit selected · F
              </button>
              <button onClick={() => setReset((v) => v + 1)}>Fit scene</button>
            </div>
          </div>
          <Viewer
            report={report}
            selected={selected}
            onSelect={setSelected}
            mode={mode}
            mix={mix}
            changedOnly={changed}
            fit={fit}
            reset={reset}
          />
          <div className="comparison">
            <span>A / BEFORE</span>
            <input
              aria-label="A to B comparison"
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={mix}
              onChange={(e) => {
                setMix(Number(e.target.value));
                setMode("Compare");
              }}
            />
            <span>B / AFTER</span>
          </div>
          <div className="legend">
            <span>− A: wireframe ghost</span>
            <span>+ B: solid geometry</span>
            <span>↗ Arrow: world-position delta</span>
            <span>? Correspondence unresolved</span>
          </div>
          <p className="note">
            Crossfade compares two states; it is not an animation or a topology
            morph. Solid colors simplify source materials.
          </p>
        </section>
        <aside className="inspector">
          <div className="section-title">SEMANTIC INSPECTOR</div>
          {record && (
            <>
              <div className="selection-head">
                <span className={"tag " + record.status}>
                  {symbols[record.status]} {record.status}
                </span>
                <h1>{record.name}</h1>
                <p>{record.type}</p>
              </div>
              <div className="confidence">
                <strong>{record.match.confidence}</strong>
                <p>
                  {record.match.evidence.join(" · ") ||
                    (record.status === "ambiguous"
                      ? "Multiple candidates remain plausible. No correspondence has been forced."
                      : "No supported correspondence found. Addition/removal is relative to this matcher.")}
                </p>
              </div>
              <dl className="relationships">
                {Object.entries(selectedEntity?.relations || {}).map(
                  ([key, ids]) => (
                    <div key={key}>
                      <dt>{key}</dt>
                      <dd>
                        {ids
                          .map(
                            (id) =>
                              sourceEntities.find((e) => e.id === id)?.name ||
                              id,
                          )
                          .join(", ") || "—"}
                      </dd>
                    </div>
                  ),
                )}
              </dl>
              {candidates.map((c, i) => (
                <div className="candidate" key={i}>
                  ?{" "}
                  {report.before.entities.find((e) => e.id === c.before)?.name}{" "}
                  ↔ {report.after.entities.find((e) => e.id === c.after)?.name}
                  <small>{c.evidence.join(" · ")}</small>
                </div>
              ))}
              {["authored", "evaluated"].map((domain) => (
                <section key={domain} className="change-section">
                  <h2>
                    {domain === "authored"
                      ? "Authored state"
                      : "Evaluated outcome"}
                  </h2>
                  {record.changes
                    .filter((c) => c.domain === domain)
                    .map((c, i) => (
                      <article className="change" key={i}>
                        <h3>{c.label}</h3>
                        <div className="values">
                          {valueRows(c.before, c.after).map((row, j) => (
                            <div className="field-delta" key={j}>
                              {row.path && <small>{row.path}</small>}
                              <div>
                                <b>A</b>
                                <span>{formatValue(row.before)}</span>
                              </div>
                              <div>
                                <b>B</b>
                                <span>{formatValue(row.after)}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                        {c.displacement && (
                          <p>
                            {c.displacement.changed_vertices} vertices displaced
                            · max {formatValue(c.displacement.max)} local units
                          </p>
                        )}
                        {c.compatible === false && (
                          <p>
                            Topology incompatible. Before/after overlay only.
                          </p>
                        )}
                      </article>
                    ))}
                  {!record.changes.some((c) => c.domain === domain) && (
                    <p className="muted">
                      {record.status === "unchanged" ||
                      record.status === "modified"
                        ? "No difference detected in compared fields."
                        : "No matched pair to compare."}
                    </p>
                  )}
                </section>
              ))}
            </>
          )}
          <details className="coverage">
            <summary>Coverage & interpretation limits</summary>
            <p>
              Derived differences are observations, not proof of which authored
              edit caused them.
            </p>
            <ul>
              {report.diff.coverage.not_compared.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
            <p>
              One saved frame and active view layer. No persistent identity
              guarantee. Numeric tolerance: 0.00001 native units.
            </p>
            <details>
              <summary>Extraction contexts</summary>
              <p>{formatValue(report.diff.context)}</p>
            </details>
          </details>
        </aside>
      </main>
      <footer>
        <span>Authored intent → evaluated outcome</span>
        <span>No uploads · No account · No telemetry</span>
        <span>INDEX [ ] &nbsp; FIT F</span>
      </footer>
    </div>
  );
}
const root = createRoot(document.getElementById("root")!);
fetch("./report.json")
  .then((r) => {
    if (!r.ok) throw Error("report.json is missing");
    return r.json();
  })
  .then((report) => {
    if (report.diff?.schema_version !== "1.0")
      throw Error("Unsupported report schema");
    root.render(<App report={report} />);
  })
  .catch((e) =>
    root.render(
      <div className="error">
        <h1>Cannot open this comparison</h1>
        <p>{e.message}</p>
        <p>
          Generate a report with <code>sce compare</code>, then use{" "}
          <code>sce serve</code>. Opening index.html directly is not supported.
        </p>
      </div>,
    ),
  );
