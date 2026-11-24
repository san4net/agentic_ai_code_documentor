const $ = (id) => document.getElementById(id);
let activeReviewId = null;
let activeSessionId = null;

function setStatus(message, kind = "") {
  const el = $("status");
  el.textContent = message;
  el.className = `status ${kind}`;
}

function renderDiff(text) {
  const root = $("diffContent");
  root.replaceChildren();
  const lines = (text || "No textual differences.").split("\n");
  for (const line of lines) {
    const span = document.createElement("span");
    span.textContent = line + "\n";
    if (line.startsWith("+") && !line.startsWith("+++")) span.className = "diff-line-add";
    else if (line.startsWith("-") && !line.startsWith("---")) span.className = "diff-line-remove";
    else if (line.startsWith("@@") || line.startsWith("+++") || line.startsWith("---")) span.className = "diff-line-meta";
    root.append(span);
  }
}

function formatTimestamp(ts) {
  if (!ts) return "Unknown time";
  const date = typeof ts === "number" ? new Date(ts * (ts < 1e12 ? 1000 : 1)) : new Date(ts);
  return Number.isNaN(date.getTime()) ? String(ts) : date.toLocaleString();
}

function renderSessionDetail(detail) {
  const titleEl = $("sessionDetailTitle");
  const metaEl = $("sessionDetailMeta");
  const bodyEl = $("sessionDetailBody");

  bodyEl.replaceChildren();

  if (!detail) {
    titleEl.textContent = "Select a session";
    metaEl.textContent = "No session selected";
    const hint = document.createElement("p");
    hint.className = "hint";
    hint.textContent = "Click any session on the left to view its state, final output, and event history.";
    bodyEl.append(hint);
    return;
  }

  const state = detail.state || {};
  titleEl.textContent = state.workflow || detail.session_id;
  metaEl.textContent = `${detail.session_id} · ${formatTimestamp(detail.last_update_time)}`;

  // 1. Session State & Output summary
  const stateBlock = document.createElement("div");
  stateBlock.className = "detail-block";
  const stateHeading = document.createElement("h4");
  stateHeading.textContent = "Session State & Metadata";
  const statePre = document.createElement("pre");
  statePre.className = "json-box";
  statePre.textContent = JSON.stringify(state, null, 2);
  stateBlock.append(stateHeading, statePre);
  bodyEl.append(stateBlock);

  // 2. Events & Workflow Outputs
  const eventsBlock = document.createElement("div");
  eventsBlock.className = "detail-block";
  const eventsHeading = document.createElement("h4");
  const events = detail.events || [];
  eventsHeading.textContent = `Events & Outputs (${events.length})`;
  eventsBlock.append(eventsHeading);
  const eventCount = detail.event_count ?? events.length;
  eventsHeading.textContent = `Connected Events (${formatEventCount(eventCount)})`;

  if (!events.length) {
    const emptyMsg = document.createElement("p");
    emptyMsg.className = "hint";
    emptyMsg.textContent = "No events recorded for this session.";
    eventsBlock.append(emptyMsg);
  } else {
    for (const ev of events) {
      const card = document.createElement("div");
      card.className = "event-item";

      const header = document.createElement("div");
      header.className = "event-item-header";
      header.textContent = `${ev.author || "system"} · ${ev.id || "event"}`;

      const badges = document.createElement("span");
      badges.className = "event-badges";
      if (ev.has_output) badges.textContent += " [output]";
      if (ev.compacted) badges.textContent += " [compacted]";
      header.append(badges);
      card.append(header);

      if (ev.output !== undefined && ev.output !== null) {
        const outPre = document.createElement("pre");
        outPre.className = "json-box";
        outPre.textContent = typeof ev.output === "string"
          ? ev.output
          : JSON.stringify(ev.output, null, 2);
        card.append(outPre);
      }

      if (ev.text) {
        const textPre = document.createElement("pre");
        textPre.className = "event-text";
        textPre.textContent = ev.text;
        card.append(textPre);
      }

      eventsBlock.append(card);
    }
  }

  bodyEl.append(eventsBlock);
}

async function selectSession(sessionId) {
  if (!sessionId) return;
  activeSessionId = sessionId;
  renderSessionList(currentSessionsCache);
  try {
    const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to load session details.");
    renderSessionDetail(data);
  } catch (error) {
    setStatus(error.message, "error");
  }
}

let currentSessionsCache = [];

function formatEventCount(count) {
  const n = Number(count ?? 0);
  return `${n} ${n === 1 ? "event" : "events"}`;
}

function renderSessionList(sessions) {
  currentSessionsCache = sessions || [];
  const listEl = $("sessionList");
  listEl.replaceChildren();

  if (!currentSessionsCache.length) {
    const empty = document.createElement("p");
    empty.className = "hint";
    empty.textContent = "No sessions found yet. Generate a README proposal to start one.";
    listEl.append(empty);
    return;
  }

  for (const sess of currentSessionsCache) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `session-row ${sess.session_id === activeSessionId ? "active" : ""}`;

    const state = sess.state || {};
    const eventCount = sess.event_count ?? (sess.events ? sess.events.length : 0);

    const topLine = document.createElement("div");
    topLine.className = "session-row-top";
    topLine.textContent = state.workflow || "adk_session";

    const countSpan = document.createElement("span");
    countSpan.className = "session-badge";
    countSpan.textContent = formatEventCount(eventCount);
    topLine.append(countSpan);

    const idLine = document.createElement("div");
    idLine.className = "session-row-sub";
    const repoLabel = state.repository_name || state.source_type || "";
    idLine.textContent = repoLabel
      ? `${repoLabel} · ${formatEventCount(eventCount)} · ${sess.session_id.slice(0, 8)}…`
      : `${formatEventCount(eventCount)} · ${sess.session_id.slice(0, 8)}…`;

    const timeLine = document.createElement("div");
    timeLine.className = "session-row-time";
    timeLine.textContent = formatTimestamp(sess.last_update_time);

    btn.append(topLine, idLine, timeLine);
    btn.addEventListener("click", () => selectSession(sess.session_id));
    listEl.append(btn);
  }
}

async function refreshSessionHistory(focusSessionId = null) {
  try {
    const response = await fetch("/api/sessions?limit=50");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Failed to load session history.");
    if (focusSessionId) activeSessionId = focusSessionId;
    renderSessionList(data.sessions || []);
    if (activeSessionId) {
      await selectSession(activeSessionId);
    }
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function api(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

$("generateButton").addEventListener("click", async () => {
  const repositoryPath = $("repositoryPath").value.trim();
  const zipPath = $("zipPath").value.trim();
  if (Boolean(repositoryPath) === Boolean(zipPath)) {
    return setStatus("Provide exactly one input: a repository folder path or a ZIP file path.", "error");
  }
  if (zipPath && (!zipPath.startsWith("/") || !zipPath.toLowerCase().endsWith(".zip"))) {
    return setStatus("Enter a fully qualified absolute path to an existing .zip file.", "error");
  }
  $("generateButton").disabled = true;
  $("reviewPanel").classList.add("hidden");
  setStatus("Scanning repository and generating the proposed README…");
  try {
    const result = await api("/api/reviews", {
      repository_path: repositoryPath || null,
      zip_path: zipPath || null,
    });
    activeReviewId = result.review_id;
    const review = result.review;
    $("reviewPath").textContent = review.readme_path;
    $("oldContent").textContent = review.old_content || "(README.md does not exist yet)";
    $("newContent").textContent = review.proposed_content;
    $("fileState").textContent = zipPath
      ? (review.readme_existed ? "README exists inside ZIP" : "README will be added to ZIP")
      : (review.readme_existed ? "Existing README will be backed up" : "New README");
    $("approvalDescription").textContent = zipPath
      ? "Accept creates a timestamped backup of the original ZIP and updates README.md inside the archive. Reject leaves the ZIP unchanged."
      : "Accept backs up the current README (if one exists) and replaces it. Reject leaves it untouched.";
    renderDiff(review.diff);
    $("reviewPanel").classList.remove("hidden");
    setStatus(zipPath
      ? "Proposal ready. The ZIP archive has not been modified. Accepting will add README.md to a backed-up copy of the archive."
      : "Proposal ready. The repository has not been modified.", "success");
    await refreshSessionHistory(result.session_id || null);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    $("generateButton").disabled = false;
  }
});

async function submitDecision(decision) {
  if (!activeReviewId) return;
  $("acceptButton").disabled = true;
  $("rejectButton").disabled = true;
  setStatus(decision === "accept" ? "Applying approved README…" : "Rejecting proposal…");
  try {
    const result = await api(`/api/reviews/${activeReviewId}/decision`, { decision });
    activeReviewId = null;
    $("reviewPanel").classList.add("hidden");
    const detail = result.backup_path ? ` Backup: ${result.backup_path}` : "";
    setStatus(`${result.message || result.status}.${detail}`, "success");
    await refreshSessionHistory(result.commit_session_id || result.review_session_id || null);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    $("acceptButton").disabled = false;
    $("rejectButton").disabled = false;
  }
}

$("acceptButton").addEventListener("click", () => submitDecision("accept"));
$("rejectButton").addEventListener("click", () => submitDecision("reject"));
$("refreshHistoryButton").addEventListener("click", () => refreshSessionHistory());

refreshSessionHistory();