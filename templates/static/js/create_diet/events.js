let eventDelegationBound = false;

function resolveRefeicaoFromActionElement(element) {
  return toInt(element?.dataset?.refeicao);
}

function bindCreateDietActionDelegation() {
  if (eventDelegationBound) {
    return;
  }
  eventDelegationBound = true;

  document.addEventListener("click", (event) => {
    const actionable = event.target.closest("[data-action]");
    if (!actionable) {
      return;
    }

    const action = actionable.dataset.action;
    const refeicao = resolveRefeicaoFromActionElement(actionable);

    if (action === "toggle-planner") {
      event.preventDefault();
      togglePlannerMetrics();
      return;
    }

    if (action === "refresh-goals") {
      event.preventDefault();
      macros_dieta_user();
      return;
    }

    if (action === "toggle-refeicao") {
      event.preventDefault();
      toggleRefeicaoCard(refeicao);
      return;
    }

    if (action === "add-food-row") {
      event.preventDefault();
      addFoodRow(refeicao);
      return;
    }

    if (action === "calc-refeicao") {
      event.preventDefault();
      macros_refeicao(refeicao);
      return;
    }

    if (action === "clear-refeicao") {
      event.preventDefault();
      limpar_refeicao(refeicao);
      return;
    }

    if (action === "select-taco-row") {
      event.preventDefault();
      const row = actionable.closest("tr");
      if (row) {
        adicionar_alimento(row);
      }
    }
  });
}

function initializeCreateDietPage() {
  const quantidadeSelect = document.getElementById("quantidade_de_refeicoes");
  if (!quantidadeSelect) {
    return;
  }

  // Prevent stale modal classes after resize/cache restore.
  setTacoCreateModalOpen(false);

  setupCopyControls();

  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    ensureMinRows(refeicao);
  }

  quantidadeSelect.addEventListener("change", () => {
    refeicoes_quanti(quantidadeSelect.value);
    macros_dieta_user();
  });

  bindMealFormSubmit();
  bindCreateDietActionDelegation();
  setupTacoSearch();
  setupTacoCreateModal();
  setupTacoCreateForm();
  initializeSummaryToggle();
  initializeMobileCollapsers();
  if (!isTacoConfigured()) {
    setTacoFeedback("API TACO indisponivel neste ambiente.", "error");
  }
  macros_dieta_user();
  ensureActiveRow();
  updateResumoDiario();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeCreateDietPage);
} else {
  initializeCreateDietPage();
}
