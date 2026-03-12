function toIntSafe(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.trunc(parsed) : 0;
}

function getElementValue(id) {
  const element = document.getElementById(id);
  return element ? String(element.value || "").trim() : "";
}

function getSelectedSex() {
  const feminino = document.getElementById("user_feminino");
  return feminino && feminino.checked ? "Feminino" : "Masculino";
}

function getSelectedOptionDataset(id) {
  const select = document.getElementById(id);
  if (!select || select.selectedIndex < 0) {
    return {};
  }

  const selectedOption = select.options[select.selectedIndex];
  return selectedOption ? selectedOption.dataset : {};
}

function gasto_dia(valor_tmb, fatorAtividade) {
  const fator = Number(fatorAtividade);
  return Number.isFinite(fator) && fator > 0 ? Math.trunc(valor_tmb * fator) : 0;
}

function calcularTmb(peso, altura, idade, sexo) {
  if (sexo === "Feminino") {
    return Math.trunc(665 + 9.6 * peso + 1.8 * altura - 4.7 * idade);
  }
  return Math.trunc(66 + 13.7 * peso + 5.0 * altura - 6.8 * idade);
}

function calcularPlanoNutricional(peso, gastoDia, objetivoSlug, sexo) {
  let calorias = gastoDia;
  let proteina = Math.trunc(peso * 2);
  let gordura = Math.trunc(peso * 1.5);
  let objetivoLabel = "Manter Peso";

  if (objetivoSlug === "cutting") {
    calorias = Math.trunc(gastoDia - 500);
    proteina = Math.trunc(peso * 2.2);
    gordura = Math.trunc(peso * 1);
    objetivoLabel = "Cutting";
  } else if (objetivoSlug === "bulking") {
    calorias = Math.trunc(gastoDia + 500);
    proteina = Math.trunc(peso * (sexo === "Feminino" ? 2.2 : 2));
    gordura = Math.trunc(peso * (sexo === "Feminino" ? 1.8 : 2));
    objetivoLabel = "Bulking";
  }

  const carboidrato = Math.trunc((calorias - (proteina * 4 + gordura * 9)) / 4);

  return {
    objetivoLabel,
    calorias,
    proteina,
    gordura,
    carboidrato,
  };
}

function markPlanAsDirty() {
  const localBackend = document.getElementById("local_dados_do_user");
  const submitButton = document.getElementById("btn_salvar_dieta");

  if (localBackend) {
    localBackend.value = "";
  }

  if (submitButton) {
    submitButton.disabled = true;
  }
}

function validarCamposTmb() {
  const pesoRaw = getElementValue("peso_user");
  const alturaRaw = getElementValue("height_user");
  const idadeRaw = getElementValue("age_user");

  if (!pesoRaw || !alturaRaw || !idadeRaw) {
    alert("Preencha peso, altura e idade antes de calcular.");
    return null;
  }

  if (alturaRaw.includes(",") || alturaRaw.includes(".")) {
    alert("A altura deve ser informada em numero inteiro, sem virgula. Exemplo: 169");
    return null;
  }

  if (!/^\d+$/.test(pesoRaw) || !/^\d+$/.test(alturaRaw) || !/^\d+$/.test(idadeRaw)) {
    alert("Peso, altura e idade devem conter apenas numeros inteiros.");
    return null;
  }

  const peso = toIntSafe(pesoRaw);
  const altura = toIntSafe(alturaRaw);
  const idade = toIntSafe(idadeRaw);

  if (peso <= 0 || altura <= 0 || idade <= 0) {
    alert("Peso, altura e idade precisam ser maiores que zero.");
    return null;
  }

  if (altura > 272 || peso > 300 || idade > 100) {
    alert("Campo(s) invalido(s). Revise os valores informados.");
    return null;
  }

  return { peso, altura, idade };
}

function botao_gerar() {
  const validacao = validarCamposTmb();
  if (!validacao) {
    return;
  }

  const { peso, altura, idade } = validacao;
  const objetivoId = Number(getElementValue("objetivo_user"));
  const nivelAtividadeId = Number(getElementValue("nivel_de_ati_user"));
  const objetivoData = getSelectedOptionDataset("objetivo_user");
  const atividadeData = getSelectedOptionDataset("nivel_de_ati_user");
  const objetivoSlug = String(objetivoData.slug || "").trim().toLowerCase();
  const fatorAtividade = Number(atividadeData.factor);
  const sexo = getSelectedSex();

  if (!objetivoId || !nivelAtividadeId || !objetivoSlug || !Number.isFinite(fatorAtividade) || fatorAtividade <= 0) {
    alert("Objetivo ou nivel de atividade invalido. Atualize os cadastros e tente novamente.");
    return;
  }

  const tmb = calcularTmb(peso, altura, idade, sexo);
  const gastoDia = gasto_dia(tmb, fatorAtividade);
  const plano = calcularPlanoNutricional(peso, gastoDia, objetivoSlug, sexo);

  const containerResultado = document.querySelector(".valor_tmb");
  const localTmbParado = document.getElementById("gasto_parado_javascript");
  const localGastoDia = document.getElementById("gasto_dia_js");
  const localObjetivo = document.getElementById("objetivo_javascript");
  const localCaloriaTotal = document.getElementById("valor_total_de_calorias_javascript");
  const localBackend = document.getElementById("local_dados_do_user");
  const submitButton = document.getElementById("btn_salvar_dieta");

  if (containerResultado) {
    containerResultado.style.display = "grid";
  }

  if (localTmbParado) {
    localTmbParado.innerText = String(tmb);
  }
  if (localGastoDia) {
    localGastoDia.innerText = String(gastoDia);
  }
  if (localObjetivo) {
    localObjetivo.innerText = plano.objetivoLabel;
  }
  if (localCaloriaTotal) {
    localCaloriaTotal.innerText = String(plano.calorias);
  }
  if (localBackend) {
    localBackend.value = [
      tmb,
      gastoDia,
      plano.calorias,
      plano.proteina,
      plano.gordura,
      plano.carboidrato,
      sexo,
    ].join(",");
  }

  if (submitButton) {
    submitButton.disabled = false;
  }
}

function bindTmbFormGuards() {
  const form = document.getElementById("tmb-form");
  if (!form) {
    return;
  }

  const watchedIds = [
    "peso_user",
    "height_user",
    "age_user",
    "objetivo_user",
    "nivel_de_ati_user",
    "user_masculino",
    "user_feminino",
  ];

  watchedIds.forEach((id) => {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }

    const eventName = element.type === "radio" || element.tagName === "SELECT" ? "change" : "input";
    element.addEventListener(eventName, markPlanAsDirty);
  });

  form.addEventListener("submit", (event) => {
    const localBackend = document.getElementById("local_dados_do_user");
    if (!localBackend || String(localBackend.value || "").trim() === "") {
      event.preventDefault();
      alert("Clique em 'Gerar taxa metabolica basal' antes de salvar a dieta.");
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bindTmbFormGuards);
} else {
  bindTmbFormGuards();
}
