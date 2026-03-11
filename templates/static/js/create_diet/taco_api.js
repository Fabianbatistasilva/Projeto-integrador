function buildTacoRow(alimento) {
  const row = document.createElement("tr");
  row.className = "row_alimentos";
  row.dataset.action = "select-taco-row";
  row.addEventListener("click", () => adicionar_alimento(row));

  const nome = document.createElement("td");
  nome.className = "td_alimento_1";
  nome.textContent = alimento.name ?? "";

  const kcal = document.createElement("td");
  kcal.className = "td_kcal";
  kcal.textContent = `${toInt(alimento.kcal)}kcal`;

  const prot = document.createElement("td");
  prot.className = "td_prot";
  prot.textContent = `${toInt(alimento.protein)}g`;

  const gord = document.createElement("td");
  gord.className = "td_gordura";
  gord.textContent = `${toInt(alimento.fat)}g`;

  const carb = document.createElement("td");
  carb.className = "td_carb";
  carb.textContent = `${toInt(alimento.carbo)}g`;

  row.appendChild(nome);
  row.appendChild(kcal);
  row.appendChild(prot);
  row.appendChild(gord);
  row.appendChild(carb);
  return row;
}

function renderTacoResults(alimentos) {
  const body = document.getElementById("alimentos_tabela_Taco");
  if (!body) {
    return;
  }

  body.innerHTML = "";

  if (!Array.isArray(alimentos) || alimentos.length === 0) {
    const emptyRow = document.createElement("tr");
    const emptyCol = document.createElement("td");
    emptyCol.colSpan = 5;
    emptyCol.textContent = "Nenhum alimento encontrado.";
    emptyCol.style.textAlign = "center";
    emptyRow.appendChild(emptyCol);
    body.appendChild(emptyRow);
    return;
  }

  alimentos.forEach((alimento) => {
    body.appendChild(buildTacoRow(alimento));
  });
}

function setTacoFeedback(message, tone = "info") {
  const feedback = document.getElementById("taco-feedback");
  if (!feedback) {
    return;
  }
  feedback.classList.remove("is-info", "is-success", "is-error");
  feedback.classList.add(tone === "error" ? "is-error" : tone === "success" ? "is-success" : "is-info");
  feedback.innerText = message || "";
}

function setTacoSearchLoading(isLoading) {
  state.tacoSearchLoading = isLoading;
  const button = document.getElementById("taco-search-btn");
  if (button) {
    button.classList.toggle("is-loading", isLoading);
    button.disabled = !isTacoConfigured() || isLoading;
    button.innerText = isLoading ? "Buscando..." : "Buscar";
  }
  syncTacoPaginationControls();
}

function setTacoCreateLoading(isLoading) {
  state.tacoCreateLoading = isLoading;
  const submitButton = document.getElementById("taco-create-submit-btn");
  if (!submitButton) {
    return;
  }

  submitButton.classList.toggle("is-loading", isLoading);
  submitButton.disabled = !isTacoConfigured() || isLoading;
  submitButton.innerText = isLoading ? "Enviando..." : "Adicionar na API";
}

function syncTacoPaginationControls() {
  const prevButton = document.getElementById("taco-prev-btn");
  const nextButton = document.getElementById("taco-next-btn");
  const pageLabel = document.getElementById("taco-page-label");
  if (!prevButton || !nextButton || !pageLabel) {
    return;
  }

  const canUse = isTacoConfigured() && !state.tacoSearchLoading;
  prevButton.disabled = !canUse || !state.tacoPrevious;
  nextButton.disabled = !canUse || !state.tacoNext;
  pageLabel.innerText = `Pagina ${state.tacoPage} (${state.tacoCount} itens)`;
}

function updateTacoPaginationState(payload, page) {
  state.tacoPage = page;
  state.tacoCount = toInt(payload?.count);
  state.tacoResultsLength = Array.isArray(payload?.results) ? payload.results.length : 0;
  state.tacoNext = payload?.next || null;
  state.tacoPrevious = payload?.previous || null;
  syncTacoPaginationControls();
}

function buildApiError(payload, statusCode, fallbackMessage) {
  const error = new Error(payload?.detail || fallbackMessage);
  error.status = statusCode;
  error.errorType = payload?.error_type || "";
  return error;
}

function getTacoErrorMessage(error, action) {
  const operation = action === "create" ? "adicionar alimento" : "buscar alimentos";
  const errorType = String(error?.errorType || "");
  const rawMessage = String(error?.message || "").trim();
  const lowerMessage = rawMessage.toLowerCase();
  if (errorType === "missing_token") {
    return "Token da API TACO nao configurado para escrita.";
  }
  if (errorType === "timeout") {
    return "A API TACO demorou para responder. Tente novamente.";
  }
  if (errorType === "connection_error") {
    return "Falha de conexao com a API TACO.";
  }
  if (errorType === "config_error") {
    return "API TACO nao configurada neste ambiente.";
  }
  if (lowerMessage === "authentication_required") {
    return "Sua sessao expirou. Faca login novamente.";
  }
  if (lowerMessage.includes("invalid token")) {
    return "Token da API TACO invalido ou expirado. Atualize TACO_API_TOKEN.";
  }
  if (lowerMessage.includes("authentication credentials were not provided")) {
    return "Token da API TACO ausente no request de escrita.";
  }
  if (error?.status === 401 || error?.status === 403) {
    return rawMessage || "Sem permissao na API TACO para esta operacao.";
  }
  return rawMessage || `Nao foi possivel ${operation} agora.`;
}

async function fetchTacoResults(searchText, page = 1) {
  if (!isTacoConfigured()) {
    throw new Error("API TACO nao configurada neste ambiente.");
  }

  const endpoint = `/api/alimentos/?search=${encodeURIComponent(searchText)}&page=${encodeURIComponent(page)}`;
  const response = await fetch(endpoint, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  let payload = {};
  try {
    payload = await response.json();
  } catch (error) {
    payload = {};
  }

  if (!response.ok) {
    throw buildApiError(payload, response.status, "Falha ao buscar alimentos.");
  }

  return {
    count: toInt(payload?.count),
    next: payload?.next || null,
    previous: payload?.previous || null,
    results: Array.isArray(payload?.results) ? payload.results : [],
  };
}

async function loadTacoResults(searchText, page = 1) {
  setTacoSearchLoading(true);
  setTacoFeedback("Buscando alimentos...", "info");

  try {
    const payload = await fetchTacoResults(searchText, page);
    state.tacoSearchTerm = String(searchText || "").trim();
    renderTacoResults(payload.results);
    updateTacoPaginationState(payload, page);

    if (payload.results.length === 0) {
      setTacoFeedback("Nenhum alimento encontrado para este filtro.", "info");
    } else {
      setTacoFeedback(
        `Lista atualizada: ${payload.results.length} itens carregados (total: ${payload.count}).`,
        "success"
      );
    }
  } catch (error) {
    setTacoFeedback(getTacoErrorMessage(error, "search"), "error");
    syncTacoPaginationControls();
  } finally {
    setTacoSearchLoading(false);
  }
}

function setupTacoSearch() {
  const form = document.getElementById("taco-search-form");
  const input = document.getElementById("taco-search-input");
  const prevButton = document.getElementById("taco-prev-btn");
  const nextButton = document.getElementById("taco-next-btn");

  if (!form || !input) {
    return;
  }

  state.tacoSearchTerm = input.value.trim();
  state.tacoPage = 1;
  state.tacoCount = document.querySelectorAll("#alimentos_tabela_Taco .row_alimentos").length;
  state.tacoResultsLength = state.tacoCount;
  state.tacoNext = null;
  state.tacoPrevious = null;
  syncTacoPaginationControls();

  const runSearch = (page = 1) => {
    loadTacoResults(input.value.trim(), page);
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!isTacoConfigured()) {
      setTacoFeedback("API TACO nao configurada neste ambiente.", "error");
      return;
    }
    if (state.tacoSearchTimer) {
      clearTimeout(state.tacoSearchTimer);
      state.tacoSearchTimer = null;
    }
    runSearch(1);
  });

  input.addEventListener("input", () => {
    if (!isTacoConfigured()) {
      return;
    }
    if (state.tacoSearchTimer) {
      clearTimeout(state.tacoSearchTimer);
    }
    state.tacoSearchTimer = setTimeout(() => {
      runSearch(1);
    }, 380);
  });

  if (prevButton) {
    prevButton.addEventListener("click", () => {
      if (!state.tacoPrevious || state.tacoSearchLoading) {
        return;
      }
      const prevPage = Math.max(1, state.tacoPage - 1);
      loadTacoResults(input.value.trim(), prevPage);
    });
  }

  if (nextButton) {
    nextButton.addEventListener("click", () => {
      if (!state.tacoNext || state.tacoSearchLoading) {
        return;
      }
      loadTacoResults(input.value.trim(), state.tacoPage + 1);
    });
  }
}

async function createTacoFood(payload) {
  if (!isTacoConfigured()) {
    throw new Error("API TACO nao configurada neste ambiente.");
  }

  const response = await fetch("/api/alimentos/criar/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
    body: JSON.stringify(payload),
  });

  let responseData = {};
  try {
    responseData = await response.json();
  } catch (error) {
    responseData = {};
  }

  if (!response.ok) {
    throw buildApiError(responseData, response.status, "Nao foi possivel adicionar alimento na API.");
  }

  return responseData;
}

function isMobileCreateMode() {
  return window.matchMedia("(max-width: 760px)").matches;
}

function setTacoCreateModalOpen(visible) {
  const form = document.getElementById("taco-create-form");
  const overlay = document.getElementById("taco-create-overlay");
  if (!form || !overlay) {
    return;
  }

  state.tacoCreateModalOpen = visible;
  form.classList.toggle("is-open", visible);
  overlay.classList.toggle("is-open", visible);
  overlay.hidden = !visible;
}

function setupTacoCreateModal() {
  const trigger = document.getElementById("open-taco-create-modal");
  const closeButton = document.getElementById("close-taco-create-modal");
  const overlay = document.getElementById("taco-create-overlay");
  const nameInput = document.getElementById("taco-create-name");

  if (!trigger) {
    return;
  }

  trigger.addEventListener("click", () => {
    if (isMobileCreateMode()) {
      setTacoCreateModalOpen(true);
      if (nameInput) {
        nameInput.focus();
      }
      return;
    }

    if (nameInput) {
      nameInput.focus();
      nameInput.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });

  if (closeButton) {
    closeButton.addEventListener("click", () => setTacoCreateModalOpen(false));
  }

  if (overlay) {
    overlay.addEventListener("click", () => setTacoCreateModalOpen(false));
  }

  window.addEventListener("resize", () => {
    if (!isMobileCreateMode() && state.tacoCreateModalOpen) {
      setTacoCreateModalOpen(false);
    }
  });
}

function setupTacoCreateForm() {
  const form = document.getElementById("taco-create-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const nameInput = document.getElementById("taco-create-name");
    const kcalInput = document.getElementById("taco-create-kcal");
    const proteinInput = document.getElementById("taco-create-protein");
    const fatInput = document.getElementById("taco-create-fat");
    const carboInput = document.getElementById("taco-create-carbo");
    const searchInput = document.getElementById("taco-search-input");

    const payload = {
      name: String(nameInput?.value || "").trim(),
      kcal: toInt(kcalInput?.value),
      protein: toInt(proteinInput?.value),
      fat: toInt(fatInput?.value),
      carbo: toInt(carboInput?.value),
    };

    if (!payload.name) {
      setTacoFeedback("Informe o nome do alimento.", "error");
      return;
    }

    if (payload.kcal < 0 || payload.protein < 0 || payload.fat < 0 || payload.carbo < 0) {
      setTacoFeedback("Macros devem ser maiores ou iguais a zero.", "error");
      return;
    }

    try {
      setTacoCreateLoading(true);
      await createTacoFood(payload);
      form.reset();
      if (state.tacoCreateModalOpen) {
        setTacoCreateModalOpen(false);
      }
      setTacoFeedback("Alimento adicionado na API TACO com sucesso.", "success");

      const searchText = (searchInput?.value || "").trim();
      const currentPage = state.tacoPage > 0 ? state.tacoPage : 1;
      await loadTacoResults(searchText, currentPage);
    } catch (error) {
      setTacoFeedback(getTacoErrorMessage(error, "create"), "error");
    } finally {
      setTacoCreateLoading(false);
    }
  });
}

