"use strict";
const $ = (id) => document.getElementById(id);
const slugs = ["revenue", "grain", "timezone"];
const money = (cents) =>
  cents == null
    ? "Unavailable"
    : new Intl.NumberFormat("en-IE", {
        style: "currency",
        currency: "EUR",
      }).format(cents / 100);
let current = null,
  reference = false,
  busy = false,
  hintIndex = 0,
  selectedTable = 0,
  activeTab = "evidence",
  requestId = 0;
const hintCounts = {};
const text = (tag, value, className) => {
  const el = document.createElement(tag);
  el.textContent = value;
  if (className) el.className = className;
  return el;
};
function slug() {
  const hash = location.hash.slice(1);
  return slugs.includes(hash) ? hash : "revenue";
}
function announce(value) {
  $("live-status").textContent = value;
}
function showError(message) {
  $("error-banner").textContent = message;
  $("error-banner").hidden = !message;
}
async function api(path) {
  const response = await fetch(path, { cache: "no-store" });
  const data = await response.json();
  if (!response.ok)
    throw new Error([data.error, data.detail].filter(Boolean).join("\n"));
  return data;
}
function saveNotes() {
  try {
    localStorage.setItem(`mrl-notes-${slug()}`, $("notes").value);
    $("notes-status").textContent = "Saved in this browser only.";
  } catch {
    $("notes-status").textContent =
      "Browser storage unavailable. Export your notes before leaving.";
  }
}
function loadNotes() {
  try {
    $("notes").value = localStorage.getItem(`mrl-notes-${slug()}`) || "";
  } catch {
    $("notes").value = "";
    $("notes-status").textContent =
      "Browser storage unavailable. Use Export Markdown.";
  }
}
function setTab(tab, focus = false) {
  activeTab = tab;
  for (const name of ["evidence", "checks", "notes"]) {
    const selected = name === tab;
    $("tab-" + name).setAttribute("aria-selected", String(selected));
    $("tab-" + name).tabIndex = selected ? 0 : -1;
    $("view-" + name).hidden = !selected;
  }
  if (focus) $("tab-" + tab).focus();
}
function renderTable() {
  const table = current.tables[selectedTable];
  const element = $("evidence-table");
  element.replaceChildren();
  if (!table) {
    $("row-count").textContent = "0 rows";
    element.append(
      text(
        "caption",
        "No evidence available. Inspect the error and repair your workspace.",
      ),
    );
    return;
  }
  const rows = table.rows;
  const columns = rows.length ? Object.keys(rows[0]) : [];
  $("row-count").textContent = `${rows.length} rows`;
  element.append(text("caption", table.name, "sr-only"));
  if (!columns.length) {
    element.append(text("caption", "No rows in this dataset."));
    return;
  }
  const head = document.createElement("thead"),
    header = document.createElement("tr");
  for (const column of columns) {
    const th = text("th", column);
    th.scope = "col";
    header.append(th);
  }
  head.append(header);
  element.append(head);
  const body = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const column of columns) {
      const value = row[column];
      tr.append(
        text(
          "td",
          value === null ? "NULL" : String(value),
          typeof value === "number" ? "number" : "",
        ),
      );
    }
    body.append(tr);
  }
  element.append(body);
}
function renderHints() {
  hintIndex = hintCounts[slug()] || 0;
  $("hint-count").textContent = `${hintIndex} / ${current.hints.length}`;
  const content = $("hint-content");
  content.replaceChildren();
  if (!hintIndex)
    content.append(
      text("p", "Form a hypothesis first. Reveal one clue when you need it."),
    );
  else
    for (let i = 0; i < hintIndex; i++)
      content.append(text("p", `${i + 1}. ${current.hints[i]}`));
  $("hint-button").disabled = hintIndex >= current.hints.length;
  $("hint-button").firstChild.textContent =
    hintIndex >= current.hints.length
      ? "All hints revealed "
      : "Reveal next hint ";
}
function render() {
  const c = current,
    complete = c.passed === c.checks.length,
    gap = c.actual_cents === null ? null : c.expected_cents - c.actual_cents;
  document.title = `${c.title} · Missing Revenue Lab`;
  $("crumb").textContent = c.id;
  $("case-number").textContent =
    `INCIDENT ${String(slugs.indexOf(c.slug) + 1).padStart(3, "0")} / 003`;
  $("category").textContent = c.category;
  $("duration").textContent = `${c.minutes} min`;
  $("case-title").replaceChildren(
    document.createTextNode(c.title),
    text("span", ".", "accent"),
  );
  $("summary").textContent = c.summary;
  $("edit-path").textContent = c.edit;
  $("expected-value").textContent = money(c.expected_cents);
  $("actual-value").textContent = money(c.actual_cents);
  $("actual-caption").textContent = reference
    ? "From the supplied reference"
    : "From your current code";
  $("gap-value").textContent =
    gap === null ? "Unavailable" : money(Math.abs(gap));
  $("gap-caption").textContent =
    gap === null
      ? "Execution needs attention"
      : gap === 0
        ? "Control totals reconcile"
        : gap < 0
          ? "Reported value exceeds expected"
          : "Expected value exceeds reported";
  $("gap-value")
    .closest("article")
    .classList.toggle("resolved", gap === 0);
  $("check-count").replaceChildren(
    document.createTextNode(String(c.passed) + " "),
    text("span", `/ ${c.checks.length}`),
  );
  $("checks-caption").textContent = reference
    ? "Reference acceptance checks"
    : "Current workspace acceptance checks";
  $("status-badge").textContent = complete
    ? "All checks pass"
    : "Needs investigation";
  $("status-badge").classList.toggle("resolved", complete);
  $("table-count").textContent = c.tables.length;
  $("check-tab-count").textContent = c.checks.length;
  $("table-select").replaceChildren(
    ...c.tables.map((table, i) => {
      const option = text("option", table.name);
      option.value = i;
      return option;
    }),
  );
  selectedTable = Math.min(selectedTable, Math.max(0, c.tables.length - 1));
  $("table-select").value = selectedTable;
  renderTable();
  $("checks-list").replaceChildren(
    ...c.checks.map((check) => {
      const item = document.createElement("details");
      item.className = `check ${check.status}`;
      const summary = document.createElement("summary");
      summary.append(
        text("span", check.status === "pass" ? "✓" : "!", "check-icon"),
        text("span", check.name.replace(/^test_/, "").replaceAll("_", " ")),
        text("span", check.status),
      );
      item.append(summary, text("p", check.detail));
      return item;
    }),
  );
  $("question").textContent = c.question;
  $("tasks").replaceChildren(...c.tasks.map((task) => text("li", task)));
  $("contract-content").replaceChildren(
    ...c.contract.map((item) => text("li", item)),
  );
  $("timeline").replaceChildren(
    ...c.timeline.map(([time, title, detail]) => {
      const item = text("article", "", "timeline-event");
      item.append(text("time", time), text("h3", title), text("p", detail));
      return item;
    }),
  );
  for (const [id, selected] of [
    ["workspace-button", !reference],
    ["reference-button", reference],
  ]) {
    $(id).classList.toggle("selected", selected);
    $(id).setAttribute("aria-pressed", String(selected));
  }
  $("solution-panel").hidden = !reference;
  $("solution-text").textContent = c.solution || "";
  $("limitation-text").textContent = c.limitation || "";
  $("solution-command").textContent =
    `python -m lab check --case ${c.slug} --solution`;
  document.querySelectorAll(".case-link").forEach((link) => {
    const active = link.dataset.case === c.slug;
    link.classList.toggle("active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  renderHints();
  setTab(activeTab);
  showError(c.execution_error || "");
}
async function refresh() {
  const thisRequest = ++requestId;
  busy = true;
  document.body.classList.add("busy");
  $("run-button").disabled = true;
  $("run-button").querySelector("span").textContent = "Running checks…";
  $("export-button").disabled = true;
  $("notes-export").disabled = true;
  $("main").setAttribute("aria-busy", "true");
  try {
    const result = await api(
      `/api/state?case=${encodeURIComponent(slug())}&solution=${reference ? 1 : 0}`,
    );
    if (thisRequest !== requestId) return;
    current = result;
    render();
    $("export-button").disabled = false;
    $("notes-export").disabled = false;
    announce(
      `${result.passed} of ${result.checks.length} checks passed in ${result.mode} mode.`,
    );
  } catch (error) {
    if (thisRequest === requestId) {
      showError(
        error.message +
          "\nIf the server stopped, restart it with python -m lab serve. Previous evidence below may be stale.",
      );
      $("actual-value").textContent = "Unavailable";
      $("gap-value").textContent = "Unavailable";
      $("check-count").textContent = "Not evaluated";
      announce("Could not run checks.");
    }
  } finally {
    if (thisRequest === requestId) {
      busy = false;
      document.body.classList.remove("busy");
      $("run-button").disabled = false;
      $("run-button").querySelector("span").textContent = "Run checks";
      $("main").setAttribute("aria-busy", "false");
    }
  }
}
function exportNotes() {
  if (
    !current ||
    current.slug !== slug() ||
    busy ||
    $("export-button").disabled
  )
    return;
  const content = `# ${current.id}: ${current.title}\n\nMode: ${current.mode}\nExpected: ${money(current.expected_cents)}\nReported: ${money(current.actual_cents)}\nChecks: ${current.passed}/${current.checks.length}\n\n## Investigation\n\n${$("notes").value || "No notes recorded."}\n\n## Check results\n\n${current.checks.map((c) => `- [${c.status === "pass" ? "x" : " "}] ${c.name}`).join("\n")}\n\nGenerated by Missing Revenue Lab. Fictional data.\n`;
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/markdown;charset=utf-8" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${current.id.toLowerCase()}-investigation.md`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  announce("Investigation notes exported.");
}
$("run-button").addEventListener("click", refresh);
$("table-select").addEventListener("change", (event) => {
  selectedTable = Number(event.target.value);
  renderTable();
});
document
  .querySelectorAll("[data-tab]")
  .forEach((button) =>
    button.addEventListener("click", () => setTab(button.dataset.tab)),
  );
document.querySelector(".tabs").addEventListener("keydown", (event) => {
  const tabs = ["evidence", "checks", "notes"];
  let next = tabs.indexOf(activeTab);
  if (event.key === "ArrowRight") next = (next + 1) % 3;
  else if (event.key === "ArrowLeft") next = (next + 2) % 3;
  else if (event.key === "Home") next = 0;
  else if (event.key === "End") next = 2;
  else return;
  event.preventDefault();
  setTab(tabs[next], true);
});
$("hint-button").addEventListener("click", () => {
  if (!current) return;
  hintCounts[slug()] = Math.min(
    (hintCounts[slug()] || 0) + 1,
    current.hints.length,
  );
  renderHints();
  announce("Hint revealed.");
});
$("contract-toggle").addEventListener("click", () => {
  const expanded =
    $("contract-toggle").getAttribute("aria-expanded") === "true";
  $("contract-toggle").setAttribute("aria-expanded", String(!expanded));
  $("contract-content").hidden = expanded;
  $("contract-toggle").lastElementChild.textContent = expanded ? "+" : "−";
});
$("reference-button").addEventListener("click", () => {
  if (!reference) $("reference-dialog").showModal();
});
$("cancel-reference").addEventListener("click", () =>
  $("reference-dialog").close(),
);
$("confirm-reference").addEventListener("click", () => {
  $("reference-dialog").close();
  reference = true;
  refresh();
});
$("workspace-button").addEventListener("click", () => {
  if (reference) {
    reference = false;
    refresh();
  }
});
$("guide-button").addEventListener("click", () =>
  $("guide-dialog").showModal(),
);
$("quick-guide").addEventListener("click", () => $("guide-dialog").showModal());
$("close-guide").addEventListener("click", () => $("guide-dialog").close());
function openVideo() {
  $("guide-dialog").close();
  $("video-dialog").showModal();
}
$("watch-video").addEventListener("click", openVideo);
$("watch-video-mobile").addEventListener("click", openVideo);
$("close-video").addEventListener("click", () => $("video-dialog").close());
$("video-dialog").addEventListener("close", () =>
  $("walkthrough-video").pause(),
);
$("notes").addEventListener("input", saveNotes);
$("export-button").addEventListener("click", exportNotes);
$("notes-export").addEventListener("click", exportNotes);
window.addEventListener("hashchange", () => {
  reference = false;
  selectedTable = 0;
  activeTab = "evidence";
  loadNotes();
  refresh();
});
document.addEventListener("keydown", (event) => {
  if (
    event.key.toLowerCase() !== "r" ||
    event.ctrlKey ||
    event.metaKey ||
    event.altKey ||
    busy ||
    document.querySelector("dialog[open]") ||
    ["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) ||
    document.activeElement.isContentEditable
  )
    return;
  event.preventDefault();
  refresh();
});
async function init() {
  try {
    const cases = await api("/api/catalog");
    $("case-nav").replaceChildren(
      ...cases.map((c, i) => {
        const link = text("a", "", "case-link");
        link.href = "#" + c.slug;
        link.dataset.case = c.slug;
        const label = document.createElement("span");
        label.append(
          text("strong", c.title),
          text("small", `${c.id} · ${c.category}`),
        );
        link.append(
          text("span", String(i + 1).padStart(2, "0"), "nav-symbol"),
          label,
        );
        return link;
      }),
    );
    loadNotes();
    await refresh();
  } catch (error) {
    showError("Could not connect to the local lab. " + error.message);
  }
}
init();
