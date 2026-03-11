function getRefeicaoSection(refeicao) {
  const suffix = REFEICAO_SUFFIX[refeicao];
  return suffix ? document.querySelector(`.refeicoes_user_${suffix}`) : null;
}

function setPlannerFeedback(message, tone = "error") {
  const feedback = document.getElementById("planner-feedback");
  if (!feedback) {
    return;
  }
  feedback.classList.remove("is-info", "is-success", "is-error");
  feedback.classList.add(tone === "error" ? "is-error" : tone === "success" ? "is-success" : "is-info");
  feedback.innerText = message || "";
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
      setPlannerFeedback("Existe quantidade preenchida sem alimento selecionado.", "error");
      setActiveRow(refeicao, row.dataset.rowId);
      return false;
    }

    if (hasFood && quantidade <= 0) {
      setPlannerFeedback("Informe a quantidade em gramas para os alimentos selecionados.", "error");
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
    setPlannerFeedback("Adicione pelo menos um alimento nessa refeicao.", "error");
    return false;
  }

  setPlannerFeedback("", "info");
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
    setPlannerFeedback("Escolha uma refeicao de destino para copiar.", "error");
    return;
  }

  if (targetRefeicao === sourceRefeicao) {
    setPlannerFeedback("Escolha uma refeicao diferente da origem.", "error");
    return;
  }

  const sourceItems = collectMealItems(sourceRefeicao);
  if (sourceItems.length === 0) {
    setPlannerFeedback("A refeicao de origem nao possui alimentos validos para copiar.", "error");
    return;
  }

  applyMealItems(targetRefeicao, sourceItems);
  const firstTargetRow = getRows(targetRefeicao)[0];
  if (firstTargetRow) {
    setActiveRow(targetRefeicao, firstTargetRow.dataset.rowId);
  }
  updateResumoDiario();
  setPlannerFeedback("Refeicao copiada com sucesso.", "success");
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
    setPlannerFeedback("Selecione uma linha da refeicao para inserir o alimento.", "error");
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
  setPlannerFeedback("Alimento inserido na refeicao selecionada.", "success");
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
      setPlannerFeedback("", "info");
    } catch (error) {
      event.preventDefault();
      setPlannerFeedback(error.message || "Nao foi possivel validar a dieta.", "error");
    }
  });
}

