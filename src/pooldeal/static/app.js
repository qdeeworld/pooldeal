const state = { obligationId: null, ended: false, recalled: false };

const byId = (id) => document.getElementById(id);
const setBusy = (button, busy, busyLabel) => {
  if (!button.dataset.label) button.dataset.label = button.textContent;
  button.disabled = busy;
  button.setAttribute("aria-busy", String(busy));
  button.textContent = busy ? busyLabel : button.dataset.label;
};
const complete = (name) => document.querySelector(`[data-stage="${name}"]`).classList.add("complete");

async function api(path, body = null) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : null,
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `Request failed: ${response.status}`);
  return payload;
}

function short(value) {
  return `${value.slice(0, 8)}…${value.slice(-6)}`;
}

async function loadStatus() {
  try {
    const status = await api("/api/status");
    const runtime = byId("runtime-label");
    runtime.textContent = status.ready
      ? `Ready · PID ${status.server_pid} · ${status.network}`
      : "Validation wallets unavailable";
    runtime.parentElement.classList.toggle("ready", status.ready);
    byId("write-button").disabled = !status.ready;
  } catch (error) {
    byId("runtime-label").textContent = error.message;
  }
}

byId("write-button").addEventListener("click", async () => {
  const button = byId("write-button");
  setBusy(button, true, "Signing and writing…");
  try {
    const result = await api("/api/write", {});
    state.obligationId = result.obligation_id;
    byId("write-evidence").textContent = `Sibyl write · PID ${result.write.pid} · session ${short(result.write.session_id)}`;
    byId("memory-explanation").textContent = result.meaning;
    complete("write");
    byId("restart-button").disabled = false;
    button.textContent = "Prior credit recorded";
  } catch (error) {
    byId("write-evidence").textContent = error.message;
    setBusy(button, false, "");
  }
});

byId("restart-button").addEventListener("click", () => {
  state.ended = true;
  byId("restart-evidence").textContent = "Session one ended. No credit amount will be sent to session two.";
  complete("restart");
  byId("restart-button").disabled = true;
  byId("restart-button").textContent = "Session ended";
  byId("recall-button").disabled = false;
});

byId("recall-button").addEventListener("click", async () => {
  const button = byId("recall-button");
  setBusy(button, true, "Starting fresh process…");
  try {
    const result = await api("/api/recall", { obligation_id: state.obligationId });
    const values = Object.values(result.proposed_split).sort((a, b) => a - b);
    byId("memory-split").textContent = `${values[0]} / ${values[1]}`;
    byId("recall-evidence").textContent = `Fresh recall · PID ${result.pid} · session ${short(result.session_id)} · digest ${short(result.obligation_digest)}`;
    state.recalled = true;
    complete("recall");
    byId("settle-button").disabled = false;
    byId("ablation-button").disabled = false;
    button.textContent = "25 / 75 recalled";
  } catch (error) {
    byId("recall-evidence").textContent = error.message;
    setBusy(button, false, "");
  }
});

byId("ablation-button").addEventListener("click", async () => {
  const button = byId("ablation-button");
  setBusy(button, true, "Removing memory…");
  try {
    const result = await api("/api/ablate", { obligation_id: state.obligationId });
    byId("ablation-result").textContent = `REFUSED · ${result.reason} · fresh PID ${result.pid}`;
    button.textContent = "Control refused safely";
  } catch (error) {
    byId("ablation-result").textContent = error.message;
    setBusy(button, false, "");
  }
});

byId("settle-button").addEventListener("click", () => {
  byId("settlement-dialog").showModal();
});

byId("settlement-dialog").addEventListener("close", async (event) => {
  if (event.target.returnValue !== "confirm") return;
  const button = byId("settle-button");
  setBusy(button, true, "Approving and settling…");
  byId("settle-evidence").textContent = "Prepared wallets are submitting exact Base Sepolia transactions…";
  try {
    const result = await api("/api/settle", { obligation_id: state.obligationId });
    const evidence = byId("settle-evidence");
    evidence.replaceChildren(document.createTextNode(`Round ${result.round_id} settled and memory consumed · `));
    result.receipts.forEach(({ label, tx }, index) => {
      if (index) evidence.append(document.createTextNode(" · "));
      const link = document.createElement("a");
      link.href = `${result.explorer}/tx/${tx}`;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = label;
      evidence.append(link);
    });
    complete("settle");
    button.textContent = "Settled and consumed";
  } catch (error) {
    byId("settle-evidence").textContent = error.message;
    setBusy(button, false, "");
  }
});

loadStatus();
