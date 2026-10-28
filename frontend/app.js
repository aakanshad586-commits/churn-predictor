"use strict";

const chartInstances = [];
const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});
const numberFormatter = new Intl.NumberFormat("en-US");
const numericFeatures = ["tenure", "MonthlyCharges"];
const categoricalFeatures = ["Contract", "InternetService", "PaymentMethod", "TechSupport"];
const modelFeatures = [...numericFeatures, ...categoricalFeatures];
const tenureGroups = ["0-12", "13-24", "25-48", "49-72"];
const chartColors = {
  retained: "#4c78a8",
  churned: "#e4572e",
  violet: "#8173df",
  muted: "#8994a8",
  grid: "rgba(130, 145, 170, .15)",
};

let customerRecords = [];
let modelState = null;

function setStatus(message, failed = false) {
  const status = document.getElementById("status");
  status.textContent = message;
  status.closest(".status-label").classList.toggle("is-error", failed);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        field += character;
      }
    } else if (character === '"' && field.length === 0) {
      quoted = true;
    } else if (character === ",") {
      row.push(field);
      field = "";
    } else if (character === "\n" || character === "\r") {
      row.push(field);
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      field = "";
      if (character === "\r" && text[index + 1] === "\n") index += 1;
    } else {
      field += character;
    }
  }

  if (quoted) throw new Error("The CSV file contains an unterminated quoted field.");
  if (field !== "" || row.length > 0) {
    row.push(field);
    if (row.some((value) => value !== "")) rows.push(row);
  }
  return rows;
}

function prepareCustomers(csvText) {
  const [headers, ...rows] = parseCsv(csvText);
  const required = [
    "customerID", "tenure", "MonthlyCharges", "TotalCharges", "Contract",
    "InternetService", "PaymentMethod", "TechSupport", "SeniorCitizen", "Churn",
  ];
  if (!headers || required.some((column) => !headers.includes(column))) {
    throw new Error("This file is missing required Telco Customer Churn columns.");
  }

  const seen = new Set();
  return rows
    .filter((values) => values.length === headers.length)
    .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index].trim()])))
    .map((customer) => {
      const tenure = Number(customer.tenure);
      const monthlyCharges = Number(customer.MonthlyCharges);
      let totalCharges = customer.TotalCharges.trim() === "" ? Number.NaN : Number(customer.TotalCharges);
      if (tenure === 0) totalCharges = 0;
      return {
        ...customer,
        tenure,
        MonthlyCharges: monthlyCharges,
        TotalCharges: totalCharges,
        SeniorCitizen: Number(customer.SeniorCitizen) === 1 ? "Yes" : "No",
        Churn: customer.Churn === "Yes" ? 1 : 0,
      };
    })
    .filter((customer) =>
      Number.isFinite(customer.tenure)
      && Number.isFinite(customer.MonthlyCharges)
      && Number.isFinite(customer.TotalCharges))
    .filter((customer) => {
      const signature = JSON.stringify(customer);
      if (seen.has(signature)) return false;
      seen.add(signature);
      return true;
    })
    .map((customer) => ({
      ...customer,
      TenureGroup: customer.tenure <= 12 ? tenureGroups[0]
        : customer.tenure <= 24 ? tenureGroups[1]
          : customer.tenure <= 48 ? tenureGroups[2]
            : customer.tenure <= 72 ? tenureGroups[3] : null,
    }))
    .filter((customer) => customer.TenureGroup !== null);
}

function filterCustomers() {
  const contract = document.getElementById("contract-filter").value;
  return contract === "All"
    ? customerRecords
    : customerRecords.filter((customer) => customer.Contract === contract);
}

function renderMetrics(records) {
  const total = records.length;
  const churned = records.reduce((sum, customer) => sum + customer.Churn, 0);
  const churnRate = total ? (churned / total) * 100 : 0;
  const averageCharge = total
    ? records.reduce((sum, customer) => sum + customer.MonthlyCharges, 0) / total
    : 0;

  document.getElementById("kpi-total-customers").textContent = numberFormatter.format(total);
  document.getElementById("kpi-churned-customers").textContent = numberFormatter.format(churned);
  document.getElementById("kpi-churn-rate").textContent = `${churnRate.toFixed(2)}%`;
  document.getElementById("kpi-average-charge").textContent = currencyFormatter.format(averageCharge);
}

function getChurnRates(records, getCategory, order = null) {
  const groups = new Map();
  records.forEach((customer) => {
    const category = getCategory(customer);
    const group = groups.get(category) ?? { count: 0, churned: 0 };
    group.count += 1;
    group.churned += customer.Churn;
    groups.set(category, group);
  });
  const labels = order
    ? order.filter((label) => groups.has(label))
    : [...groups.keys()].sort((a, b) => a.localeCompare(b));
  return {
    labels,
    values: labels.map((label) => Number(((groups.get(label).churned / groups.get(label).count) * 100).toFixed(2))),
  };
}

function baseChartOptions() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 400 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#20283a",
        titleColor: "#f6f7fb",
        bodyColor: "#c5cedd",
        borderColor: "rgba(192,204,225,.14)",
        borderWidth: 1,
        padding: 10,
        displayColors: false,
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { display: false },
        ticks: { color: chartColors.muted, font: { family: "DM Sans", size: 10 } },
      },
      y: {
        beginAtZero: true,
        max: 100,
        grid: { color: chartColors.grid },
        border: { display: false },
        ticks: {
          color: chartColors.muted,
          font: { family: "DM Sans", size: 10 },
          callback: (value) => `${value}%`,
        },
      },
    },
  };
}

function renderCharts(records) {
  chartInstances.forEach((chart) => chart.destroy());
  chartInstances.length = 0;

  const churned = records.reduce((sum, customer) => sum + customer.Churn, 0);
  const retained = records.length - churned;
  document.getElementById("retention-summary").textContent = numberFormatter.format(retained);

  const distributionChart = new Chart(document.getElementById("chart-churn-distribution"), {
    type: "doughnut",
    data: {
      labels: ["Retained", "Churned"],
      datasets: [{
        data: [retained, churned],
        backgroundColor: [chartColors.retained, chartColors.churned],
        borderColor: "#1b2232",
        borderWidth: 4,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "74%",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#20283a",
          titleColor: "#f6f7fb",
          bodyColor: "#c5cedd",
          borderColor: "rgba(192,204,225,.14)",
          borderWidth: 1,
          padding: 10,
        },
      },
    },
  });
  chartInstances.push(distributionChart);

  const contractRates = getChurnRates(records, (customer) => customer.Contract);
  chartInstances.push(new Chart(document.getElementById("chart-churn-contract"), {
    type: "bar",
    data: {
      labels: contractRates.labels,
      datasets: [{
        data: contractRates.values,
        backgroundColor: "#8173df",
        hoverBackgroundColor: "#a092f2",
        borderRadius: 6,
        borderSkipped: false,
        maxBarThickness: 54,
      }],
    },
    options: baseChartOptions(),
  }));

  const tenureRates = getChurnRates(
    records.filter((customer) => customer.TenureGroup !== null),
    (customer) => customer.TenureGroup,
    tenureGroups,
  );
  chartInstances.push(new Chart(document.getElementById("chart-churn-tenure"), {
    type: "bar",
    data: {
      labels: tenureRates.labels,
      datasets: [{
        data: tenureRates.values,
        backgroundColor: "#4c78a8",
        hoverBackgroundColor: "#6d95c0",
        borderRadius: 6,
        borderSkipped: false,
        maxBarThickness: 54,
      }],
    },
    options: baseChartOptions(),
  }));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  })[character]);
}

function renderCustomers() {
  const search = document.getElementById("customer-search").value.trim().toLowerCase();
  const churnFilter = document.getElementById("churn-filter").value;
  const matching = filterCustomers().filter((customer) => {
    const statusMatches = churnFilter === "all"
      || (churnFilter === "churned" && customer.Churn === 1)
      || (churnFilter === "active" && customer.Churn === 0);
    const searchable = [
      customer.customerID,
      customer.Contract,
      customer.PaymentMethod,
      customer.InternetService,
    ].join(" ").toLowerCase();
    return statusMatches && searchable.includes(search);
  });

  const rows = matching.slice(0, 100);
  const tableBody = document.getElementById("customer-table-body");
  if (!rows.length) {
    tableBody.innerHTML = '<tr><td class="table-message" colspan="6">No customers match your filters.</td></tr>';
  } else {
    tableBody.innerHTML = rows.map((customer) => {
      const status = customer.Churn
        ? '<span class="status-badge status-churned">Churned</span>'
        : '<span class="status-badge status-active">Retained</span>';
      return `<tr>
        <td><div class="customer-cell"><span class="customer-initial">${escapeHtml(customer.customerID.slice(0, 2).toUpperCase())}</span><span><span class="customer-name">${escapeHtml(customer.customerID)}</span><br><span class="customer-id">${escapeHtml(customer.InternetService)} · ${escapeHtml(customer.gender)}</span></span></div></td>
        <td>${escapeHtml(customer.Contract)}</td>
        <td>${customer.tenure} ${customer.tenure === 1 ? "month" : "months"}</td>
        <td>${escapeHtml(customer.PaymentMethod)}</td>
        <td>${currencyFormatter.format(customer.MonthlyCharges)}</td>
        <td>${status}</td>
      </tr>`;
    }).join("");
  }

  document.getElementById("table-result-count").textContent =
    `Showing ${numberFormatter.format(rows.length)} of ${numberFormatter.format(matching.length)} matching customers`;
  document.getElementById("customer-count").textContent =
    `${numberFormatter.format(matching.length)} customers`;
}

function seededRandom(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function splitStratified(records) {
  const random = seededRandom(42);
  const train = [];
  const test = [];
  [0, 1].forEach((label) => {
    const group = records.filter((customer) => customer.Churn === label);
    for (let index = group.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(random() * (index + 1));
      [group[index], group[swapIndex]] = [group[swapIndex], group[index]];
    }
    const testCount = Math.ceil(group.length * 0.2);
    test.push(...group.slice(0, testCount));
    train.push(...group.slice(testCount));
  });
  return { train, test };
}

function featureLayout(trainingRecords) {
  const numericStats = Object.fromEntries(numericFeatures.map((feature) => {
    const mean = trainingRecords.reduce((sum, row) => sum + row[feature], 0) / trainingRecords.length;
    const variance = trainingRecords.reduce((sum, row) => sum + (row[feature] - mean) ** 2, 0)
      / trainingRecords.length;
    return [feature, { mean, scale: Math.sqrt(variance) || 1 }];
  }));
  const categories = Object.fromEntries(categoricalFeatures.map((feature) => [
    feature,
    [...new Set(trainingRecords.map((row) => row[feature]))].sort(),
  ]));
  return { numericStats, categories };
}

function encodeCustomer(customer, layout) {
  const encoded = numericFeatures.map((feature) =>
    (customer[feature] - layout.numericStats[feature].mean) / layout.numericStats[feature].scale);
  categoricalFeatures.forEach((feature) => {
    layout.categories[feature].forEach((category) => {
      encoded.push(customer[feature] === category ? 1 : 0);
    });
  });
  return encoded;
}

function sigmoid(value) {
  if (value >= 0) return 1 / (1 + Math.exp(-Math.min(value, 40)));
  const exponential = Math.exp(Math.max(value, -40));
  return exponential / (1 + exponential);
}

function solveLinearSystem(matrix, vector) {
  const size = vector.length;
  const rows = matrix.map((row, index) => [...row, vector[index]]);
  for (let pivot = 0; pivot < size; pivot += 1) {
    let best = pivot;
    for (let row = pivot + 1; row < size; row += 1) {
      if (Math.abs(rows[row][pivot]) > Math.abs(rows[best][pivot])) best = row;
    }
    [rows[pivot], rows[best]] = [rows[best], rows[pivot]];
    const divisor = rows[pivot][pivot];
    if (Math.abs(divisor) < 1e-12) continue;
    for (let column = pivot; column <= size; column += 1) rows[pivot][column] /= divisor;
    for (let row = 0; row < size; row += 1) {
      if (row === pivot) continue;
      const factor = rows[row][pivot];
      for (let column = pivot; column <= size; column += 1) {
        rows[row][column] -= factor * rows[pivot][column];
      }
    }
  }
  return rows.map((row) => row[size]);
}

function fitLogisticRegression(records, layout) {
  const inputs = records.map((customer) => encodeCustomer(customer, layout));
  const labels = records.map((customer) => customer.Churn);
  const dimensions = inputs[0].length + 1;
  const weights = Array(dimensions).fill(0);
  const l2Strength = 1;

  for (let iteration = 0; iteration < 80; iteration += 1) {
    const gradient = Array(dimensions).fill(0);
    const hessian = Array.from({ length: dimensions }, () => Array(dimensions).fill(0));
    inputs.forEach((features, rowIndex) => {
      const vector = [1, ...features];
      const probability = sigmoid(vector.reduce((sum, value, index) => sum + value * weights[index], 0));
      const error = probability - labels[rowIndex];
      const variance = Math.max(probability * (1 - probability), 1e-8);
      vector.forEach((value, row) => {
        gradient[row] += value * error;
        vector.forEach((otherValue, column) => {
          hessian[row][column] += value * otherValue * variance;
        });
      });
    });
    for (let index = 1; index < dimensions; index += 1) {
      gradient[index] += l2Strength * weights[index];
      hessian[index][index] += l2Strength;
    }
    const adjustment = solveLinearSystem(hessian, gradient);
    let largestChange = 0;
    adjustment.forEach((value, index) => {
      weights[index] -= value;
      largestChange = Math.max(largestChange, Math.abs(value));
    });
    if (largestChange < 1e-7) break;
  }
  return { weights, layout };
}

function predictProbability(customer, model) {
  const features = [1, ...encodeCustomer(customer, model.layout)];
  return sigmoid(features.reduce((sum, value, index) => sum + value * model.weights[index], 0));
}

function trainAndScoreModel(records) {
  const split = splitStratified(records);
  const layout = featureLayout(split.train);
  const model = fitLogisticRegression(split.train, layout);
  let correct = 0;
  let truePositive = 0;
  let falsePositive = 0;
  let falseNegative = 0;
  split.test.forEach((customer) => {
    const predicted = predictProbability(customer, model) >= 0.5 ? 1 : 0;
    if (predicted === customer.Churn) correct += 1;
    if (predicted === 1 && customer.Churn === 1) truePositive += 1;
    if (predicted === 1 && customer.Churn === 0) falsePositive += 1;
    if (predicted === 0 && customer.Churn === 1) falseNegative += 1;
  });
  return {
    model,
    accuracy: correct / split.test.length,
    precision: truePositive + falsePositive ? truePositive / (truePositive + falsePositive) : 0,
    recall: truePositive + falseNegative ? truePositive / (truePositive + falseNegative) : 0,
  };
}

function fillOptions(select, values) {
  select.replaceChildren(...values.map((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    return option;
  }));
}

function retentionTips(customer) {
  return [
    customer.Contract === "Month-to-month"
      ? "Offer a discounted annual plan."
      : "Offer a renewal benefit before the current contract ends.",
    customer.TechSupport === "No"
      ? "Offer a tech-support plan or a personal setup session."
      : "Schedule a proactive check-in about the customer's support experience.",
    customer.tenure <= 12
      ? "Provide an onboarding check-in and early loyalty offer."
      : "Recognize the customer's tenure with a personalized loyalty benefit.",
  ];
}

function predictCustomer(event) {
  event.preventDefault();
  if (!modelState) return;

  const customer = {
    Contract: document.getElementById("predict-contract").value,
    tenure: Number(document.getElementById("predict-tenure").value),
    MonthlyCharges: Number(document.getElementById("predict-monthly-charges").value),
    InternetService: document.getElementById("predict-internet").value,
    PaymentMethod: document.getElementById("predict-payment").value,
    TechSupport: document.getElementById("predict-tech-support").value,
  };
  const probability = predictProbability(customer, modelState.model) * 100;
  const risk = probability < 35 ? "Low" : probability < 60 ? "Medium" : "High";
  const result = document.getElementById("prediction-result");
  result.className = `prediction-result risk-${risk.toLowerCase()}`;
  result.innerHTML = `
    <div class="risk-result-heading"><span class="risk-icon">!</span><div><p class="risk-eyebrow">ESTIMATED CHURN PROBABILITY</p><p class="risk-value">${probability.toFixed(1)}% <span>${risk} risk</span></p></div></div>
    <h4>Suggested retention ideas</h4>
    <ul>${retentionTips(customer).map((tip) => `<li>${escapeHtml(tip)}</li>`).join("")}</ul>`;
  result.hidden = false;
}

function renderDashboard() {
  const filtered = filterCustomers();
  renderMetrics(filtered);
  renderCharts(filtered);
  renderCustomers();
  document.getElementById("insight-count").textContent =
    `Calculations based on ${numberFormatter.format(filtered.length)} customers`;
}

async function loadDashboard() {
  const refreshButton = document.getElementById("refresh-button");
  refreshButton.disabled = true;
  refreshButton.classList.add("is-loading");
  setStatus("Loading Telco dataset…");
  try {
    let response = await fetch("../WA_Fn-UseC_-Telco-Customer-Churn.csv", { cache: "no-store" });
    let usingSample = false;
    if (!response.ok) {
      response = await fetch("../sample_telco_churn_data.csv", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(
          `Could not load the Telco CSV (${response.status}) or sample_telco_churn_data.csv.`,
        );
      }
      usingSample = true;
    }
    const csvText = await response.text();
    customerRecords = prepareCustomers(csvText);
    if (!customerRecords.length) throw new Error("The Telco CSV contains no valid customer records.");

    modelState = trainAndScoreModel(customerRecords);
    fillOptions(
      document.getElementById("predict-internet"),
      [...new Set(customerRecords.map((customer) => customer.InternetService))].sort(),
    );
    fillOptions(
      document.getElementById("predict-payment"),
      [...new Set(customerRecords.map((customer) => customer.PaymentMethod))].sort(),
    );
    const sortedTenures = customerRecords.map((customer) => customer.tenure).sort((a, b) => a - b);
    const middle = Math.floor(sortedTenures.length / 2);
    const medianTenure = sortedTenures.length % 2
      ? sortedTenures[middle]
      : Math.round((sortedTenures[middle - 1] + sortedTenures[middle]) / 2);
    const averageMonthlyCharge = customerRecords.reduce(
      (sum, customer) => sum + customer.MonthlyCharges,
      0,
    ) / customerRecords.length;
    document.getElementById("predict-tenure").value = medianTenure;
    document.getElementById("tenure-value").textContent =
      `${medianTenure} ${medianTenure === 1 ? "month" : "months"}`;
    const monthlyChargeInput = document.getElementById("predict-monthly-charges");
    monthlyChargeInput.max = Math.max(...customerRecords.map((customer) => customer.MonthlyCharges)).toFixed(2);
    monthlyChargeInput.value = averageMonthlyCharge.toFixed(2);
    document.getElementById("model-accuracy").textContent = `${(modelState.accuracy * 100).toFixed(2)}%`;
    document.getElementById("model-precision").textContent = `${(modelState.precision * 100).toFixed(2)}%`;
    document.getElementById("model-recall").textContent = `${(modelState.recall * 100).toFixed(2)}%`;
    renderDashboard();
    const warning = document.getElementById("dataset-warning");
    warning.hidden = !usingSample;
    warning.textContent = usingSample ? "Using SAMPLE data. Results are not real." : "";
    setStatus(usingSample ? "Sample dataset loaded" : "Telco dataset loaded");
  } catch (error) {
    console.error("Unable to load dashboard data:", error);
    setStatus("Unable to load data", true);
    document.getElementById("customer-table-body").innerHTML =
      '<tr><td class="table-message" colspan="6">Could not load the CSV dataset. Run the local web server from the project folder and open the frontend directory.</td></tr>';
    document.getElementById("table-result-count").textContent = "Data unavailable";
  } finally {
    refreshButton.disabled = false;
    refreshButton.classList.remove("is-loading");
  }
}

document.getElementById("footer-year").textContent = new Date().getFullYear();
document.getElementById("customer-search").addEventListener("input", renderCustomers);
document.getElementById("churn-filter").addEventListener("change", renderCustomers);
document.getElementById("contract-filter").addEventListener("change", renderDashboard);
document.getElementById("predict-tenure").addEventListener("input", (event) => {
  document.getElementById("tenure-value").textContent =
    `${event.target.value} ${Number(event.target.value) === 1 ? "month" : "months"}`;
});
document.getElementById("prediction-form").addEventListener("submit", predictCustomer);
document.getElementById("refresh-button").addEventListener("click", loadDashboard);

loadDashboard();
