const REFRESH_MS = 30000;

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else node.setAttribute(k, v);
  }
  for (const child of children) {
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

function setBadge(cardId, state, text) {
  const card = document.getElementById(cardId);
  const badge = card.querySelector("[data-badge]");
  badge.textContent = text;
  badge.setAttribute("data-state", state);
}

function setBody(cardId, node) {
  const card = document.getElementById(cardId);
  const body = card.querySelector("[data-body]");
  body.replaceChildren(node);
}

function emptyState(message) {
  return el("p", { class: "empty-state" }, [message]);
}

function statusPill(status) {
  const map = {
    verified: ["OK", "pill-ok"],
    integrity_failed: ["ÉCHEC INTÉGRITÉ", "pill-warn"],
    in_progress: ["EN COURS", "pill-neutral"],
    unknown: ["INCONNU", "pill-neutral"],
    no_custody_log: ["SANS LOG", "pill-neutral"],
  };
  const [label, cls] = map[status] || [status || "—", "pill-neutral"];
  return el("span", { class: `pill ${cls}` }, [label]);
}

function stepChip(step) {
  const ok = /ok/i.test(step.result) && !/fail/i.test(step.result);
  return el("span", { class: "step-chip" }, [`${step.tool}: ${ok ? "OK" : step.result}`]);
}

async function loadOsint() {
  try {
    const data = await fetch("/api/osint/investigations").then((r) => r.json());
    if (!data.configured) {
      setBadge("card-osint", "unset", "non configuré");
      setBody("card-osint", emptyState("FLOWSINT_API_URL non défini — voir .env.example."));
      return;
    }
    if (data.error) {
      setBadge("card-osint", "warn", "erreur");
      setBody("card-osint", el("p", { class: "error-state" }, [data.error]));
      return;
    }
    setBadge("card-osint", "ok", `${data.investigations.length} investigation(s)`);
    if (data.investigations.length === 0) {
      setBody("card-osint", emptyState("Aucune investigation."));
      return;
    }
    const table = el("table", {}, [
      el("thead", {}, [el("tr", {}, ["Nom", "Statut", "Sketches", "Rôle", "MAJ"].map((h) => el("th", {}, [h])))]),
      el(
        "tbody",
        {},
        data.investigations.map((inv) =>
          el("tr", {}, [
            el("td", {}, [inv.name || "—"]),
            el("td", {}, [inv.status || "—"]),
            el("td", {}, [String(inv.sketches ?? "—")]),
            el("td", {}, [inv.role || "—"]),
            el("td", {}, [inv.last_updated_at ? new Date(inv.last_updated_at).toLocaleString("fr-FR") : "—"]),
          ])
        )
      ),
    ]);
    setBody("card-osint", table);
  } catch (e) {
    setBadge("card-osint", "warn", "injoignable");
    setBody("card-osint", el("p", { class: "error-state" }, [String(e)]));
  }
}

async function loadForensics() {
  try {
    const data = await fetch("/api/forensics/cases").then((r) => r.json());
    if (!data.configured) {
      setBadge("card-forensics", "unset", "non configuré");
      setBody("card-forensics", emptyState("FORENSICS_SOURCES non défini — voir .env.example."));
      return;
    }
    setBadge("card-forensics", "ok", `${data.cases.length} case(s)`);
    if (data.cases.length === 0) {
      setBody("card-forensics", emptyState("Aucune case trouvée."));
      return;
    }
    const table = el("table", {}, [
      el("thead", {}, [el("tr", {}, ["Outil", "Case", "Statut", "Étiquette", "Opérateur"].map((h) => el("th", {}, [h])))]),
      el(
        "tbody",
        {},
        data.cases.map((c) =>
          el("tr", {}, [
            el("td", {}, [c.tool]),
            el("td", {}, [c.case]),
            el("td", {}, [statusPill(c.status)]),
            el("td", {}, [c.evidence_label || "—"]),
            el("td", {}, [c.operator || "—"]),
          ])
        )
      ),
    ]);
    setBody("card-forensics", table);
  } catch (e) {
    setBadge("card-forensics", "warn", "erreur");
    setBody("card-forensics", el("p", { class: "error-state" }, [String(e)]));
  }
}

async function loadPentest() {
  try {
    const data = await fetch("/api/pentest/reports").then((r) => r.json());
    if (!data.configured) {
      setBadge("card-pentest", "unset", "non configuré");
      setBody("card-pentest", emptyState("PENTEST_REPORTS_DIR non défini — voir .env.example."));
      return;
    }
    setBadge("card-pentest", "ok", `${data.reports.length} rapport(s)`);
    if (data.reports.length === 0) {
      setBody("card-pentest", emptyState("Aucun rapport trouvé."));
      return;
    }
    const table = el("table", {}, [
      el("thead", {}, [el("tr", {}, ["Horodatage", "Cible", "Étapes"].map((h) => el("th", {}, [h])))]),
      el(
        "tbody",
        {},
        data.reports.map((r) =>
          el("tr", {}, [
            el("td", {}, [r.timestamp]),
            el("td", {}, [r.target || "—"]),
            el(
              "td",
              { class: "step-list" },
              r.steps.length ? r.steps.map(stepChip) : [emptyState("—")]
            ),
          ])
        )
      ),
    ]);
    setBody("card-pentest", table);
  } catch (e) {
    setBadge("card-pentest", "warn", "erreur");
    setBody("card-pentest", el("p", { class: "error-state" }, [String(e)]));
  }
}

async function loadBlueteam() {
  try {
    const data = await fetch("/api/blueteam/pivots").then((r) => r.json());
    if (!data.configured) {
      setBadge("card-blueteam", "unset", "non configuré");
      setBody("card-blueteam", emptyState("Fichier de pivots introuvable — lancer export_pivots.py."));
      return;
    }
    setBadge("card-blueteam", "ok", `${data.pivots.length} pivot(s)`);
    if (data.pivots.length === 0) {
      setBody("card-blueteam", emptyState("Aucun pivot warning/critical pour le moment."));
      return;
    }
    const table = el("table", {}, [
      el("thead", {}, [el("tr", {}, ["Sévérité", "IP", "Type", "Message"].map((h) => el("th", {}, [h])))]),
      el(
        "tbody",
        {},
        data.pivots.map((p) =>
          el("tr", {}, [
            el("td", {}, [el("span", { class: `pill ${p.severity === "critical" ? "pill-warn" : "pill-neutral"}` }, [p.severity])]),
            el("td", {}, [p.ip]),
            el("td", {}, [p.alert_type || "—"]),
            el("td", {}, [p.message || "—"]),
          ])
        )
      ),
    ]);
    setBody("card-blueteam", table);
  } catch (e) {
    setBadge("card-blueteam", "warn", "erreur");
    setBody("card-blueteam", el("p", { class: "error-state" }, [String(e)]));
  }
}

async function refreshAll() {
  await Promise.all([loadOsint(), loadForensics(), loadPentest(), loadBlueteam()]);
  document.getElementById("last-refresh").textContent =
    "dernière mise à jour : " + new Date().toLocaleTimeString("fr-FR");
}

refreshAll();
setInterval(refreshAll, REFRESH_MS);
