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
  tacoSearchTerm: "",
  tacoPage: 1,
  tacoCount: 0,
  tacoResultsLength: 0,
  tacoNext: null,
  tacoPrevious: null,
  tacoSearchTimer: null,
  tacoSearchLoading: false,
  tacoCreateLoading: false,
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

