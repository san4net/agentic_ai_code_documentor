const $ = (id) => document.getElementById(id);
let activeReviewId = null;

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
    if (line.startsWith("+" ) && !line.startsWith("+++")) span.className = "diff-line-add";
    else if (line.startsWith("-") && !line.startsWith("---")) span.className = "diff-line-remove";
    else if (line.startsWith("@@") || line.startsWith("+++") || line.startsWith("---")) span.className = "diff-line-meta";
    root.append(span);
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
  if (!repositoryPath) return setStatus("Enter an absolute repository path.", "error");
  $("generateButton").disabled = true;
  $("reviewPanel").classList.add("hidden");
  setStatus("Scanning repository and generating the proposed README…");
  try {
    const result = await api("/api/reviews", { repository_path: repositoryPath });
    activeReviewId = result.review_id;
    const review = result.review;
    $("reviewPath").textContent = review.readme_path;
    $("oldContent").textContent = review.old_content || "(README.md does not exist yet)";
    $("newContent").textContent = review.proposed_content;
    $("fileState").textContent = review.readme_existed ? "Existing README will be backed up" : "New README";
    renderDiff(review.diff);
    $("reviewPanel").classList.remove("hidden");
    setStatus("Proposal ready. The repository has not been modified.", "success");
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
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    $("acceptButton").disabled = false;
    $("rejectButton").disabled = false;
  }
}

$("acceptButton").addEventListener("click", () => submitDecision("accept"));
$("rejectButton").addEventListener("click", () => submitDecision("reject"));
