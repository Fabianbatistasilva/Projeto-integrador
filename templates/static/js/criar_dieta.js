const REFEICAO_SUFFIX = {
  1: "one",
  2: "two",
  3: "tree",
  4: "four",
  5: "five",
  6: "six",
};

const TOTAL_REFEICOES = 6;
const MIN_ROWS_PER_MEAL = 1;
const SUMMARY_MOBILE_BREAKPOINT = "(max-width: 1180px)";
const MOBILE_COLLAPSE_BREAKPOINT = "(max-width: 760px)";
const state = {
  activeRefeicao: null,
  activeRowId: "",
  rowCounter: 0,
  tacoCreateModalOpen: false,
  summaryCollapsed: false,
  wasSummaryMobile: null,
  wasCollapseMobile: null,
};

function parseNumeric(value) {
  const normalized = String(value ?? "")
    .replace("kcal", "")
    .replace("g", "")
    .replace(",", ".")
    .replace(/[^0-9.-]/g, "");
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

function toInt(value) {
  return Math.trunc(parseNumeric(value));
}

function getCookie(name) {
  const prefix = `${name}=`;
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const rawCookie of cookies) {
    const cookie = rawCookie.trim();
    if (cookie.startsWith(prefix)) {
      return decodeURIComponent(cookie.substring(prefix.length));
    }
  }
  return "";
}

function isTacoConfigured() {
  const panel = document.querySelector(".table-panel[data-taco-configured]");
  return panel ? panel.dataset.tacoConfigured !== "0" : true;
}

function getSummaryElements() {
  return {
    sideColumn: document.getElementById("side_column"),
    panel: document.getElementById("summary_panel"),
    button: document.getElementById("summary_toggle_btn"),
  };
}

function updateSummaryToggleText(collapsed) {
  const { button } = getSummaryElements();
  if (!button) {
    return;
  }
  button.innerText = collapsed ? "Mostrar resumo do dia" : "Ocultar resumo do dia";
  button.setAttribute("aria-expanded", collapsed ? "false" : "true");
}

function setSummaryCollapsed(collapsed) {
  const { sideColumn, panel, button } = getSummaryElements();
  if (!sideColumn || !panel || !button) {
    return;
  }

  state.summaryCollapsed = collapsed;
  sideColumn.classList.toggle("is-collapsed", collapsed);
  panel.hidden = collapsed;
  updateSummaryToggleText(collapsed);
}

function isSummaryMobileMode() {
  return window.matchMedia(SUMMARY_MOBILE_BREAKPOINT).matches;
}

function initializeSummaryToggle() {
  const { button } = getSummaryElements();
  if (!button) {
    return;
  }

  const mobileNow = isSummaryMobileMode();
  state.wasSummaryMobile = mobileNow;
  setSummaryCollapsed(mobileNow);

  button.addEventListener("click", () => {
    setSummaryCollapsed(!state.summaryCollapsed);
  });

  window.addEventListener("resize", () => {
    const mobileCurrent = isSummaryMobileMode();
    if (mobileCurrent !== state.wasSummaryMobile) {
      state.wasSummaryMobile = mobileCurrent;
      setSummaryCollapsed(mobileCurrent);
    }
  });
}

function isMobileCollapseMode() {
  return window.matchMedia(MOBILE_COLLAPSE_BREAKPOINT).matches;
}

function updatePlannerToggleText(collapsed) {
  const button = document.getElementById("planner_toggle_btn");
  if (!button) {
    return;
  }
  button.innerText = collapsed ? "Mostrar metas" : "Reduzir metas";
  button.setAttribute("aria-expanded", collapsed ? "false" : "true");
}

function setPlannerCollapsed(collapsed) {
  const panel = document.querySelector(".planner-panel");
  const content = document.getElementById("planner_metrics_block");
  if (!panel || !content) {
    return;
  }

  panel.classList.toggle("planner-metrics-collapsed", collapsed);
  content.hidden = collapsed;
  updatePlannerToggleText(collapsed);
}

function updateRefToggleText(refeicao, collapsed) {
  const button = document.querySelector(`.ref-toggle-btn[data-ref-toggle='${refeicao}']`);
  if (!button) {
    return;
  }
  button.innerText = collapsed ? "Expandir" : "Reduzir";
  button.setAttribute("aria-expanded", collapsed ? "false" : "true");
}

function setRefeicaoCollapsed(refeicao, collapsed) {
  const card = getRefeicaoSection(refeicao);
  const content = document.getElementById(`ref_content_${refeicao}`);
  if (!card || !content) {
    return;
  }

  card.classList.toggle("is-collapsed", collapsed);
  content.hidden = collapsed;
  updateRefToggleText(refeicao, collapsed);
}

function togglePlannerMetrics() {
  const panel = document.querySelector(".planner-panel");
  const collapsed = !panel?.classList.contains("planner-metrics-collapsed");
  setPlannerCollapsed(collapsed);
}

function toggleRefeicaoCard(refeicao) {
  const refeicaoInt = toInt(refeicao);
  if (refeicaoInt < 1 || refeicaoInt > TOTAL_REFEICOES) {
    return;
  }
  const card = getRefeicaoSection(refeicaoInt);
  const collapsed = !card?.classList.contains("is-collapsed");
  setRefeicaoCollapsed(refeicaoInt, collapsed);
}

function collapseOtherMealsOnMobile() {
  const visibleMeals = [];
  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    if (isRefeicaoVisible(refeicao)) {
      visibleMeals.push(refeicao);
    }
  }

  if (visibleMeals.length === 0) {
    return;
  }

  const keepOpen = visibleMeals[0];
  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    if (!isRefeicaoVisible(refeicao)) {
      setRefeicaoCollapsed(refeicao, false);
      continue;
    }
    setRefeicaoCollapsed(refeicao, refeicao !== keepOpen);
  }
}

function initializeMobileCollapsers() {
  const applyCollapseMode = () => {
    const mobileNow = isMobileCollapseMode();
    if (state.wasCollapseMobile === null) {
      state.wasCollapseMobile = mobileNow;
      if (mobileNow) {
        collapseOtherMealsOnMobile();
      }
      if (!mobileNow) {
        setPlannerCollapsed(false);
        for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
          setRefeicaoCollapsed(refeicao, false);
        }
      }
      return;
    }

    if (mobileNow !== state.wasCollapseMobile) {
      state.wasCollapseMobile = mobileNow;
      if (mobileNow) {
        collapseOtherMealsOnMobile();
      }
      if (!mobileNow) {
        setPlannerCollapsed(false);
        for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
          setRefeicaoCollapsed(refeicao, false);
        }
      }
    }
  };

  applyCollapseMode();
  window.addEventListener("resize", applyCollapseMode);
}

function setText(id, text) {
  const element = document.getElementById(id);
  if (element) {
    element.innerText = text;
  }
}

function getRefeicaoSection(refeicao) {
  const suffix = REFEICAO_SUFFIX[refeicao];
  return suffix ? document.querySelector(`.refeicoes_user_${suffix}`) : null;
}

function isRefeicaoVisible(refeicao) {
  const section = getRefeicaoSection(refeicao);
  if (!section) {
    return false;
  }
  return section.style.display !== "none";
}

function getMacroOutputElements(refeicao) {
  const suffix = REFEICAO_SUFFIX[refeicao];
  if (!suffix) {
    return null;
  }

  return {
    kcal: document.getElementById(`calorias_da_ref_${suffix}`),
    prot: document.getElementById(`proteina_da_ref_${suffix}`),
    gord: document.getElementById(`gordura_da_ref_${suffix}`),
    carb: document.getElementById(`carboidratos_da_ref_${suffix}`),
  };
}

function getFoodList(refeicao) {
  return document.getElementById(`food_list_ref_${refeicao}`);
}

function getRows(refeicao) {
  const list = getFoodList(refeicao);
  if (!list) {
    return [];
  }
  return Array.from(list.querySelectorAll(".dynamic-food-row"));
}

function getRowElement(refeicao, rowId) {
  if (!rowId) {
    return null;
  }
  const list = getFoodList(refeicao);
  if (!list) {
    return null;
  }
  return list.querySelector(`.dynamic-food-row[data-row-id='${rowId}']`);
}

function getRowQuantityInput(row) {
  return row?.querySelector(".food-qty");
}

function getRowNameLabel(row) {
  return row?.querySelector(".food-name");
}

function getMinRowsForMeal(refeicao) {
  return refeicao >= 1 && refeicao <= TOTAL_REFEICOES ? MIN_ROWS_PER_MEAL : 1;
}

function createRowId() {
  state.rowCounter += 1;
  return `row-${state.rowCounter}`;
}

function setRowFoodData(row, alimento) {
  if (!row) {
    return;
  }

  row.dataset.name = String(alimento.nome ?? "").trim();
  row.dataset.kcalBase = String(toInt(alimento.kcalBase));
  row.dataset.protBase = String(toInt(alimento.protBase));
  row.dataset.gordBase = String(toInt(alimento.gordBase));
  row.dataset.carbBase = String(toInt(alimento.carbBase));

  const label = getRowNameLabel(row);
  if (label) {
    label.innerText = row.dataset.name;
  }
}

function clearRowData(row) {
  if (!row) {
    return;
  }

  row.dataset.name = "";
  row.dataset.kcalBase = "0";
  row.dataset.protBase = "0";
  row.dataset.gordBase = "0";
  row.dataset.carbBase = "0";

  const label = getRowNameLabel(row);
  if (label) {
    label.innerText = "";
  }

  const qty = getRowQuantityInput(row);
  if (qty) {
    qty.value = "";
  }
}

function rowHasFood(row) {
  return String(row?.dataset?.name ?? "").trim() !== "";
}

function getRowQuantity(row) {
  return toInt(getRowQuantityInput(row)?.value);
}

function calculateRowMacros(row) {
  if (!row || !rowHasFood(row)) {
    return { kcal: 0, prot: 0, gord: 0, carb: 0 };
  }

  const quantidade = getRowQuantity(row);
  if (quantidade <= 0) {
    return { kcal: 0, prot: 0, gord: 0, carb: 0 };
  }

  const fator = quantidade / 100;
  return {
    kcal: Math.trunc(fator * toInt(row.dataset.kcalBase)),
    prot: Math.trunc(fator * toInt(row.dataset.protBase)),
    gord: Math.trunc(fator * toInt(row.dataset.gordBase)),
    carb: Math.trunc(fator * toInt(row.dataset.carbBase)),
  };
}

function clearRowHighlight() {
  document.querySelectorAll(".food-row-active").forEach((row) => {
    row.classList.remove("food-row-active");
  });
}

function updateSlotDestinoInfo() {
  const info = document.getElementById("slot_destino_info");
  if (!info) {
    return;
  }

  const activeRow = getActiveRow();
  if (!activeRow) {
    info.innerText = "Destino: selecione uma linha da refeicao.";
    return;
  }

  const ordinal = toInt(activeRow.dataset.rowOrder);
  info.innerText = `Destino atual: ${state.activeRefeicao}a refeicao, alimento ${ordinal}.`;
}

function setActiveRow(refeicao, rowId) {
  const row = getRowElement(refeicao, rowId);
  if (!row || !isRefeicaoVisible(refeicao)) {
    return;
  }

  clearRowHighlight();
  row.classList.add("food-row-active");

  state.activeRefeicao = refeicao;
  state.activeRowId = rowId;
  updateSlotDestinoInfo();
}

function getActiveRow() {
  if (!state.activeRefeicao || !state.activeRowId) {
    return null;
  }
  const row = getRowElement(state.activeRefeicao, state.activeRowId);
  if (!row || !isRefeicaoVisible(state.activeRefeicao)) {
    return null;
  }
  return row;
}

function getVisibleRows() {
  const rows = [];
  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    if (!isRefeicaoVisible(refeicao)) {
      continue;
    }
    getRows(refeicao).forEach((row) => {
      rows.push({ refeicao, row });
    });
  }
  return rows;
}

function findFirstVisibleRow() {
  const rows = getVisibleRows();
  return rows.length > 0 ? rows[0] : null;
}

function findFirstEmptyVisibleRow() {
  return getVisibleRows().find(({ row }) => !rowHasFood(row)) || null;
}

function findNextEmptyVisibleRow(refeicao, rowId) {
  const rows = getVisibleRows();
  const startIndex = rows.findIndex(
    ({ refeicao: ref, row }) => ref === refeicao && row.dataset.rowId === rowId
  );

  if (startIndex < 0) {
    return findFirstEmptyVisibleRow();
  }

  for (let index = startIndex + 1; index < rows.length; index += 1) {
    if (!rowHasFood(rows[index].row)) {
      return rows[index];
    }
  }

  for (let index = 0; index < startIndex; index += 1) {
    if (!rowHasFood(rows[index].row)) {
      return rows[index];
    }
  }

  return null;
}

function ensureActiveRow() {
  const current = getActiveRow();
  if (current) {
    return;
  }

  const empty = findFirstEmptyVisibleRow();
  if (empty) {
    setActiveRow(empty.refeicao, empty.row.dataset.rowId);
    return;
  }

  const first = findFirstVisibleRow();
  if (first) {
    setActiveRow(first.refeicao, first.row.dataset.rowId);
    return;
  }

  updateSlotDestinoInfo();
}

function createFoodRowElement(refeicao, preset = null) {
  const row = document.createElement("div");
  row.className = "food-row dynamic-food-row";
  row.dataset.refeicao = String(refeicao);
  row.dataset.rowId = createRowId();

  const rowOrder = getRows(refeicao).length + 1;
  row.dataset.rowOrder = String(rowOrder);

  const nameLabel = document.createElement("label");
  nameLabel.className = "food-name";

  const qty = document.createElement("input");
  qty.type = "number";
  qty.min = "0";
  qty.placeholder = "Quantidade (g)";
  qty.className = "food-qty";

  const actions = document.createElement("div");
  actions.className = "food-row-actions";

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "btn-row-remove";
  removeButton.innerText = "Remover";

  actions.appendChild(removeButton);
  row.appendChild(nameLabel);
  row.appendChild(qty);
  row.appendChild(actions);

  row.tabIndex = 0;

  row.addEventListener("click", () => {
    setActiveRow(refeicao, row.dataset.rowId);
  });

  row.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      setActiveRow(refeicao, row.dataset.rowId);
    }
  });

  qty.addEventListener("focus", () => {
    setActiveRow(refeicao, row.dataset.rowId);
  });

  qty.addEventListener("input", () => {
    updateResumoDiario();
  });

  removeButton.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    removeFoodRow(refeicao, row.dataset.rowId);
  });

  if (preset) {
    setRowFoodData(row, {
      nome: preset.name,
      kcalBase: preset.kcal_base,
      protBase: preset.prot_base,
      gordBase: preset.gord_base,
      carbBase: preset.carb_base,
    });
    qty.value = String(toInt(preset.quantidade));
  } else {
    clearRowData(row);
  }

  return row;
}

function refreshMealRowOrder(refeicao) {
  getRows(refeicao).forEach((row, index) => {
    row.dataset.rowOrder = String(index + 1);
  });
  updateSlotDestinoInfo();
}

function addFoodRow(refeicao, preset = null, focusNew = true) {
  const list = getFoodList(refeicao);
  if (!list) {
    return null;
  }

  const row = createFoodRowElement(refeicao, preset);
  list.appendChild(row);
  refreshMealRowOrder(refeicao);

  if (focusNew) {
    setActiveRow(refeicao, row.dataset.rowId);
    const qty = getRowQuantityInput(row);
    if (qty) {
      qty.focus();
    }
  }

  updateResumoDiario();
  return row;
}

function ensureMinRows(refeicao) {
  const minRows = getMinRowsForMeal(refeicao);
  while (getRows(refeicao).length < minRows) {
    addFoodRow(refeicao, null, false);
  }
}

function removeFoodRow(refeicao, rowId) {
  const row = getRowElement(refeicao, rowId);
  if (!row) {
    return;
  }

  const minRows = getMinRowsForMeal(refeicao);
  const rows = getRows(refeicao);

  if (rows.length <= minRows) {
    clearRowData(row);
    setActiveRow(refeicao, row.dataset.rowId);
    clearRefeicaoTotals(refeicao);
    updateResumoDiario();
    return;
  }

  const wasActive =
    state.activeRefeicao === refeicao && state.activeRowId === row.dataset.rowId;

  row.remove();
  refreshMealRowOrder(refeicao);
  clearRefeicaoTotals(refeicao);

  if (wasActive) {
    const first = getRows(refeicao)[0];
    if (first) {
      setActiveRow(refeicao, first.dataset.rowId);
    } else {
      ensureActiveRow();
    }
  }

  updateResumoDiario();
}

function clearMealRows(refeicao) {
  const rows = getRows(refeicao);
  const minRows = getMinRowsForMeal(refeicao);

  rows.forEach((row, index) => {
    if (index < minRows) {
      clearRowData(row);
    } else {
      row.remove();
    }
  });

  ensureMinRows(refeicao);
  refreshMealRowOrder(refeicao);
}

function getRefeicaoQuantidade(refeicao) {
  return getRows(refeicao).reduce((acc, row) => {
    if (!rowHasFood(row)) {
      return acc;
    }
    return acc + getRowQuantity(row);
  }, 0);
}

function getRefeicaoMacrosUI(refeicao) {
  const outputs = getMacroOutputElements(refeicao);
  if (!outputs) {
    return { kcal: 0, prot: 0, gord: 0, carb: 0 };
  }

  return {
    kcal: toInt(outputs.kcal?.innerText),
    prot: toInt(outputs.prot?.innerText),
    gord: toInt(outputs.gord?.innerText),
    carb: toInt(outputs.carb?.innerText),
  };
}

function validateRefeicao(refeicao) {
  const rows = getRows(refeicao);
  let foodCount = 0;

  for (const row of rows) {
    const hasFood = rowHasFood(row);
    const quantidade = getRowQuantity(row);

    if (!hasFood && quantidade > 0) {
      alert("Existe quantidade preenchida sem alimento selecionado.");
      setActiveRow(refeicao, row.dataset.rowId);
      return false;
    }

    if (hasFood && quantidade <= 0) {
      alert("Informe a quantidade em gramas para os alimentos selecionados.");
      const qty = getRowQuantityInput(row);
      if (qty) {
        qty.focus();
      }
      setActiveRow(refeicao, row.dataset.rowId);
      return false;
    }

    if (hasFood && quantidade > 0) {
      foodCount += 1;
    }
  }

  if (foodCount === 0) {
    alert("Adicione pelo menos um alimento nessa refeicao.");
    return false;
  }

  return true;
}

function updateRefeicaoTotals(refeicao, totals) {
  const outputs = getMacroOutputElements(refeicao);
  if (!outputs) {
    return;
  }

  if (outputs.kcal) outputs.kcal.innerText = String(totals.kcal);
  if (outputs.prot) outputs.prot.innerText = String(totals.prot);
  if (outputs.gord) outputs.gord.innerText = String(totals.gord);
  if (outputs.carb) outputs.carb.innerText = String(totals.carb);
}

function clearRefeicaoTotals(refeicao) {
  const outputs = getMacroOutputElements(refeicao);
  if (!outputs) {
    return;
  }

  if (outputs.kcal) outputs.kcal.innerText = "";
  if (outputs.prot) outputs.prot.innerText = "";
  if (outputs.gord) outputs.gord.innerText = "";
  if (outputs.carb) outputs.carb.innerText = "";
}

function macros_refeicao(numeroDaRef) {
  const refeicao = toInt(numeroDaRef);
  if (refeicao < 1 || refeicao > TOTAL_REFEICOES) {
    return;
  }

  if (!validateRefeicao(refeicao)) {
    return;
  }

  const totals = { kcal: 0, prot: 0, gord: 0, carb: 0 };

  getRows(refeicao).forEach((row) => {
    const rowTotals = calculateRowMacros(row);
    totals.kcal += rowTotals.kcal;
    totals.prot += rowTotals.prot;
    totals.gord += rowTotals.gord;
    totals.carb += rowTotals.carb;
  });

  updateRefeicaoTotals(refeicao, totals);
  updateResumoDiario();
}

function limpar_refeicao(numeroDaRef) {
  const refeicao = toInt(numeroDaRef);
  if (refeicao < 1 || refeicao > TOTAL_REFEICOES) {
    return;
  }

  clearMealRows(refeicao);
  clearRefeicaoTotals(refeicao);

  const firstRow = getRows(refeicao)[0];
  if (firstRow && isRefeicaoVisible(refeicao)) {
    setActiveRow(refeicao, firstRow.dataset.rowId);
  }

  updateResumoDiario();
}

function collectMealItems(refeicao) {
  const items = [];
  getRows(refeicao).forEach((row) => {
    const nome = String(row.dataset.name ?? "").trim();
    const quantidade = getRowQuantity(row);
    if (!nome || quantidade <= 0) {
      return;
    }

    items.push({
      nome,
      quantidade,
      kcalBase: toInt(row.dataset.kcalBase),
      protBase: toInt(row.dataset.protBase),
      gordBase: toInt(row.dataset.gordBase),
      carbBase: toInt(row.dataset.carbBase),
    });
  });
  return items;
}

function applyMealItems(targetRefeicao, items) {
  const quantidadeSelect = document.getElementById("quantidade_de_refeicoes");
  if (quantidadeSelect) {
    const atual = toInt(quantidadeSelect.value);
    if (targetRefeicao > atual) {
      quantidadeSelect.value = String(targetRefeicao);
      refeicoes_quanti(quantidadeSelect.value);
      macros_dieta_user();
    }
  }

  clearMealRows(targetRefeicao);
  clearRefeicaoTotals(targetRefeicao);

  let rows = getRows(targetRefeicao);
  items.forEach((item, index) => {
    let row = rows[index];
    if (!row) {
      row = addFoodRow(targetRefeicao, null, false);
      rows = getRows(targetRefeicao);
    }

    setRowFoodData(row, item);
    const qty = getRowQuantityInput(row);
    if (qty) {
      qty.value = String(item.quantidade);
    }
  });

  rows = getRows(targetRefeicao);
  rows.forEach((row, index) => {
    if (index >= items.length) {
      if (index < getMinRowsForMeal(targetRefeicao)) {
        clearRowData(row);
      } else {
        row.remove();
      }
    }
  });

  ensureMinRows(targetRefeicao);
  refreshMealRowOrder(targetRefeicao);
  clearRefeicaoTotals(targetRefeicao);
  macros_refeicao(targetRefeicao);
}

function copyMealTo(sourceRefeicao) {
  const targetSelect = document.getElementById(`copy_target_ref_${sourceRefeicao}`);
  const targetRefeicao = toInt(targetSelect?.value);

  if (targetRefeicao < 1 || targetRefeicao > TOTAL_REFEICOES) {
    alert("Escolha uma refeicao de destino para copiar.");
    return;
  }

  if (targetRefeicao === sourceRefeicao) {
    alert("Escolha uma refeicao diferente da origem.");
    return;
  }

  const sourceItems = collectMealItems(sourceRefeicao);
  if (sourceItems.length === 0) {
    alert("A refeicao de origem nao possui alimentos validos para copiar.");
    return;
  }

  applyMealItems(targetRefeicao, sourceItems);
  const firstTargetRow = getRows(targetRefeicao)[0];
  if (firstTargetRow) {
    setActiveRow(targetRefeicao, firstTargetRow.dataset.rowId);
  }
  updateResumoDiario();
}

function setupCopyControls() {
  const containers = document.querySelectorAll(".copy-controls[data-copy-source]");
  containers.forEach((container) => {
    const sourceRefeicao = toInt(container.dataset.copySource);
    if (sourceRefeicao < 1 || sourceRefeicao > TOTAL_REFEICOES) {
      return;
    }

    container.innerHTML = "";

    const select = document.createElement("select");
    select.id = `copy_target_ref_${sourceRefeicao}`;
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Copiar para...";
    select.appendChild(placeholder);

    for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
      if (refeicao === sourceRefeicao) {
        continue;
      }
      const option = document.createElement("option");
      option.value = String(refeicao);
      option.textContent = `${refeicao}a refeicao`;
      select.appendChild(option);
    }

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Copiar ref";
    button.addEventListener("click", () => copyMealTo(sourceRefeicao));

    container.appendChild(select);
    container.appendChild(button);
  });
}

function updateResumoDiario() {
  let totalQuantidade = 0;
  let totalKcal = 0;
  let totalProt = 0;
  let totalGord = 0;
  let totalCarb = 0;

  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    const visible = isRefeicaoVisible(refeicao);
    const row = document.getElementById(`summary_ref_${refeicao}`);
    if (row) {
      row.style.display = visible ? "grid" : "none";
    }

    if (!visible) {
      continue;
    }

    const quantidade = getRefeicaoQuantidade(refeicao);
    const macros = getRefeicaoMacrosUI(refeicao);

    setText(`summary_ref_${refeicao}_qty`, `${quantidade} g`);
    setText(`summary_ref_${refeicao}_kcal`, `${macros.kcal} kcal`);

    totalQuantidade += quantidade;
    totalKcal += macros.kcal;
    totalProt += macros.prot;
    totalGord += macros.gord;
    totalCarb += macros.carb;
  }

  setText("summary_day_qty", `${totalQuantidade} g`);
  setText("summary_day_kcal", `${totalKcal} kcal`);
  setText("summary_day_prot", `${totalProt} g`);
  setText("summary_day_gord", `${totalGord} g`);
  setText("summary_day_carb", `${totalCarb} g`);
}

function refeicoes_quanti(quantidade) {
  const quantidadeNum = toInt(quantidade);
  const limite = quantidadeNum >= 2 && quantidadeNum <= TOTAL_REFEICOES ? quantidadeNum : TOTAL_REFEICOES;

  for (let refeicao = 1; refeicao <= TOTAL_REFEICOES; refeicao += 1) {
    const section = getRefeicaoSection(refeicao);
    if (section) {
      section.style.display = refeicao <= limite ? "" : "none";
    }
  }

  if (isMobileCollapseMode()) {
    collapseOtherMealsOnMobile();
  }

  ensureActiveRow();
  updateResumoDiario();
  return limite;
}

function macros_dieta_user() {
  const proteinaTotal = toInt(document.getElementById("valores_total_de_proteina")?.innerText);
  const gorduraTotal = toInt(document.getElementById("valores_total_de_gordura")?.innerText);
  const carboTotal = toInt(document.getElementById("valores_total_de_carboidratos")?.innerText);
  const caloriasTotal = toInt(document.getElementById("valor_total_das_kcal")?.innerText);

  const quantidadeRefeicoes = document.getElementById("quantidade_de_refeicoes")?.value;
  const quantidade = refeicoes_quanti(quantidadeRefeicoes);

  if (!quantidade) {
    return;
  }

  const proteinaPorRef = Math.trunc(proteinaTotal / quantidade);
  const gorduraPorRef = Math.trunc(gorduraTotal / quantidade);
  const carboPorRef = Math.trunc(carboTotal / quantidade);
  const caloriasPorRef = Math.trunc(caloriasTotal / quantidade);

  setText("proteina_max_ref_user", String(proteinaPorRef));
  setText("gordura_max_ref_user", String(gorduraPorRef));
  setText("carboidratos_max_ref_user", String(carboPorRef));
  setText("calorias_max_ref_user", String(caloriasPorRef));

  updateResumoDiario();
}

function readAlimentoDaTabela(alimentoTabela) {
  const nome = alimentoTabela.querySelector(".td_alimento_1")?.innerText?.trim() || "";

  return {
    nome,
    kcal: toInt(alimentoTabela.querySelector(".td_kcal")?.innerText),
    prot: toInt(alimentoTabela.querySelector(".td_prot")?.innerText),
    gord: toInt(alimentoTabela.querySelector(".td_gordura")?.innerText),
    carb: toInt(alimentoTabela.querySelector(".td_carb")?.innerText),
  };
}

function adicionar_alimento(alimentoTabela) {
  if (!alimentoTabela) {
    return;
  }

  const alimento = readAlimentoDaTabela(alimentoTabela);
  if (!alimento.nome) {
    return;
  }

  let row = getActiveRow();
  if (!row) {
    const empty = findFirstEmptyVisibleRow();
    if (empty) {
      setActiveRow(empty.refeicao, empty.row.dataset.rowId);
      row = empty.row;
    }
  }

  if (!row) {
    const first = findFirstVisibleRow();
    if (first) {
      setActiveRow(first.refeicao, first.row.dataset.rowId);
      row = first.row;
    }
  }

  if (!row || !state.activeRefeicao) {
    alert("Selecione uma linha da refeicao para inserir o alimento.");
    return;
  }

  const wasEmpty = !rowHasFood(row);
  setRowFoodData(row, {
    nome: alimento.nome,
    kcalBase: alimento.kcal,
    protBase: alimento.prot,
    gordBase: alimento.gord,
    carbBase: alimento.carb,
  });

  const qty = getRowQuantityInput(row);
  if (qty && toInt(qty.value) <= 0) {
    qty.focus();
  }

  if (wasEmpty) {
    const nextEmpty = findNextEmptyVisibleRow(state.activeRefeicao, row.dataset.rowId);
    if (nextEmpty) {
      setActiveRow(nextEmpty.refeicao, nextEmpty.row.dataset.rowId);
    } else {
      const newRow = addFoodRow(state.activeRefeicao, null, false);
      if (newRow) {
        setActiveRow(state.activeRefeicao, newRow.dataset.rowId);
      }
    }
  }

  updateResumoDiario();
}

function buildPayloadForSubmit() {
  const selectedMeals = toInt(document.getElementById("quantidade_de_refeicoes")?.value) || TOTAL_REFEICOES;
  const meals = [];

  for (let refeicao = 1; refeicao <= selectedMeals; refeicao += 1) {
    const rows = getRows(refeicao);
    const items = [];

    for (const row of rows) {
      const nome = String(row.dataset.name ?? "").trim();
      const quantidade = getRowQuantity(row);

      if (!nome && quantidade <= 0) {
        continue;
      }

      if (!nome && quantidade > 0) {
        setActiveRow(refeicao, row.dataset.rowId);
        throw new Error("Existe quantidade preenchida sem alimento selecionado.");
      }

      if (nome && quantidade <= 0) {
        setActiveRow(refeicao, row.dataset.rowId);
        const qtyInput = getRowQuantityInput(row);
        if (qtyInput) {
          qtyInput.focus();
        }
        throw new Error("Todos os alimentos selecionados precisam de quantidade em gramas.");
      }

      items.push({
        name: nome,
        quantidade,
        kcal_base: toInt(row.dataset.kcalBase),
        prot_base: toInt(row.dataset.protBase),
        gord_base: toInt(row.dataset.gordBase),
        carb_base: toInt(row.dataset.carbBase),
      });
    }

    meals.push({ refeicao, items });
  }

  const totalItems = meals.reduce((acc, meal) => acc + meal.items.length, 0);
  if (totalItems <= 0) {
    throw new Error("Adicione alimentos para montar sua dieta.");
  }

  return {
    selected_meals: selectedMeals,
    meals,
  };
}

function bindMealFormSubmit() {
  const form = document.getElementById("meal-form");
  const payloadInput = document.getElementById("diet_payload");

  if (!form || !payloadInput) {
    return;
  }

  form.addEventListener("submit", (event) => {
    try {
      const payload = buildPayloadForSubmit();
      payloadInput.value = JSON.stringify(payload);
    } catch (error) {
      event.preventDefault();
      alert(error.message || "Nao foi possivel validar a dieta.");
    }
  });
}

function buildTacoRow(alimento) {
  const row = document.createElement("tr");
  row.className = "row_alimentos";
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

async function fetchTacoResults(searchText) {
  if (!isTacoConfigured()) {
    throw new Error("API TACO nao configurada neste ambiente.");
  }

  const endpoint = `/api/alimentos/?search=${encodeURIComponent(searchText)}`;
  const response = await fetch(endpoint, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  if (!response.ok) {
    throw new Error("Falha ao buscar alimentos.");
  }

  const payload = await response.json();
  return Array.isArray(payload.results) ? payload.results : [];
}

function setupTacoSearch() {
  const form = document.getElementById("taco-search-form");
  const input = document.getElementById("taco-search-input");

  if (!form || !input) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isTacoConfigured()) {
      alert("API TACO nao configurada neste ambiente.");
      return;
    }

    try {
      const results = await fetchTacoResults(input.value.trim());
      renderTacoResults(results);
    } catch (error) {
      alert("Nao foi possivel buscar alimentos agora.");
    }
  });
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
    throw new Error(responseData.detail || "Nao foi possivel adicionar alimento na API.");
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
      alert("Informe o nome do alimento.");
      return;
    }

    if (payload.kcal < 0 || payload.protein < 0 || payload.fat < 0 || payload.carbo < 0) {
      alert("Macros devem ser maiores ou iguais a zero.");
      return;
    }

    try {
      await createTacoFood(payload);
      form.reset();
      if (state.tacoCreateModalOpen) {
        setTacoCreateModalOpen(false);
      }
      alert("Alimento adicionado na API TACO com sucesso.");

      const results = await fetchTacoResults(searchInput?.value?.trim() || "");
      renderTacoResults(results);
    } catch (error) {
      alert(error.message || "Falha ao adicionar alimento na API TACO.");
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
  setupTacoSearch();
  setupTacoCreateModal();
  setupTacoCreateForm();
  initializeSummaryToggle();
  initializeMobileCollapsers();
  macros_dieta_user();
  ensureActiveRow();
  updateResumoDiario();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeCreateDietPage);
} else {
  initializeCreateDietPage();
}
