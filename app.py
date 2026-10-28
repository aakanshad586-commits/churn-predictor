from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


st.set_page_config(page_title="Customer Churn Dashboard", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {
        --ink: #172033;
        --muted: #788398;
        --violet: #7065d6;
        --canvas: #f4f6fb;
    }

    html, body, [class*="css"] {
        font-family: "DM Sans", sans-serif;
    }
    .stApp {
        background:
            radial-gradient(ellipse at 87% 2%, rgba(119, 105, 220, .09), transparent 31rem),
            var(--canvas);
        color: var(--ink);
    }
    [data-testid="stHeader"] {
        background: rgba(244, 246, 251, .82);
        backdrop-filter: blur(14px);
    }
    [data-testid="stToolbar"] { right: 1.5rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(165deg, #171d2d 0%, #111827 100%);
        border-right: 1px solid rgba(255,255,255,.07);
    }
    [data-testid="stSidebar"] * { color: #e7eaf2; }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #222b3c;
        border-color: rgba(255,255,255,.13);
        border-radius: 10px;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #aab4c6;
        font-size: .78rem;
        line-height: 1.6;
    }
    .block-container {
        max-width: 1500px;
        padding: 2.2rem 3rem 3rem;
    }
    h1, h2, h3, [data-testid="stMetricValue"] {
        font-family: "Manrope", "DM Sans", sans-serif;
        color: var(--ink);
        letter-spacing: -.035em;
    }
    .hero {
        position: relative;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 1.5rem;
        margin: .15rem 0 1.6rem;
        padding: 1.65rem 1.8rem;
        overflow: hidden;
        background: linear-gradient(115deg, #1a2032 0%, #272d49 65%, #39345d 100%);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 18px;
        box-shadow: 0 16px 38px rgba(27, 33, 54, .12);
    }
    .hero::after {
        position: absolute;
        top: -110px;
        right: 6%;
        width: 250px;
        height: 250px;
        border: 1px solid rgba(205,197,255,.16);
        border-radius: 50%;
        box-shadow: 0 0 0 32px rgba(205,197,255,.035), 0 0 0 66px rgba(205,197,255,.025);
        content: "";
        pointer-events: none;
    }
    .hero-copy, .hero-source { position: relative; z-index: 1; }
    .hero-eyebrow {
        margin: 0 0 .6rem;
        color: #b7adff;
        font-size: .67rem;
        font-weight: 700;
        letter-spacing: .16em;
        text-transform: uppercase;
    }
    .hero h1 {
        margin: 0;
        color: #fff;
        font-size: clamp(1.8rem, 3vw, 2.5rem);
        font-weight: 700;
        line-height: 1.15;
    }
    .hero-subtitle {
        margin: .6rem 0 0;
        color: #c1c8d8;
        font-size: .91rem;
    }
    .hero-source {
        display: flex;
        flex: 0 0 auto;
        align-items: center;
        gap: .55rem;
        padding: .58rem .8rem;
        color: #e6e9f2;
        background: rgba(255,255,255,.08);
        border: 1px solid rgba(255,255,255,.13);
        border-radius: 999px;
        font-size: .72rem;
    }
    .source-dot { width: 7px; height: 7px; background: #7dd8b1; border-radius: 50%; }
    [data-testid="stMetric"] {
        min-height: 128px;
        padding: 1.12rem 1.2rem;
        background: #fff;
        border: 1px solid #e8ebf3;
        border-radius: 14px;
        box-shadow: 0 5px 16px rgba(28, 38, 63, .045);
        transition: transform .18s ease, box-shadow .18s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(28, 38, 63, .08);
    }
    [data-testid="stMetricLabel"] p {
        color: #79849a;
        font-size: .8rem;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #20283a;
        font-size: clamp(1.5rem, 2.2vw, 2rem);
        font-weight: 700;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,.94);
        border-color: #e8ebf3 !important;
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(28, 38, 63, .04);
    }
    [data-testid="stImage"] img {
        border-radius: 10px;
    }
    [data-testid="stForm"] {
        padding: 1rem 1.15rem 1.1rem;
        background: #fff;
        border: 1px solid #e8ebf3;
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(28, 38, 63, .04);
    }
    [data-testid="stBaseButton-primary"] {
        min-height: 2.7rem;
        padding: 0 1.3rem;
        background: linear-gradient(110deg, #6e63d5, #8576e8);
        border: 0;
        border-radius: 9px;
        box-shadow: 0 5px 12px rgba(112,101,214,.22);
        font-weight: 600;
    }
    [data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(110deg, #5f55c5, #7666d9);
        border: 0;
    }
    [data-baseweb="select"] > div, [data-testid="stNumberInput"] input {
        border-color: #e1e5ef;
        border-radius: 9px;
    }
    [data-testid="stSlider"] [role="slider"] {
        background: var(--violet);
        border-color: var(--violet);
    }
    [data-testid="stExpander"] {
        background: #fff;
        border: 1px solid #e8ebf3;
        border-radius: 12px;
    }
    .section-kicker {
        margin: .2rem 0 .3rem;
        color: #7569d7;
        font-size: .68rem;
        font-weight: 700;
        letter-spacing: .13em;
        text-transform: uppercase;
    }
    .section-note { margin: 0 0 1rem; color: var(--muted); font-size: .88rem; }
    .risk-result {
        margin: 1rem 0;
        padding: 1.05rem 1.2rem;
        background: #fff;
        border: 1px solid #e8ebf3;
        border-left: 4px solid #42a77a;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(28, 38, 63, .04);
    }
    .risk-result.medium { border-left-color: #e3a23d; }
    .risk-result.high { border-left-color: #dd5b5b; }
    .risk-label { margin: 0 0 .2rem; color: #788398; font-size: .74rem; font-weight: 600; }
    .risk-value { margin: 0; color: #20283a; font: 700 1.35rem "Manrope", sans-serif; }
    .risk-value span { margin-left: .4rem; font: 600 .82rem "DM Sans", sans-serif; }
    .retention-heading { margin: 1.1rem 0 .4rem; color: #39445a; font-size: .9rem; font-weight: 700; }
    .app-footer {
        margin-top: 2rem;
        padding-top: 1rem;
        color: #8690a2;
        border-top: 1px solid #e4e8f0;
        font-size: .75rem;
        text-align: center;
    }
    @media (max-width: 850px) {
        .block-container { padding: 1.3rem 1.2rem 2rem; }
        .hero { align-items: flex-start; flex-direction: column; padding: 1.35rem; }
        .hero-source { font-size: .66rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

PROJECT_DIR = Path(__file__).resolve().parent
MAIN_DATA_FILE = PROJECT_DIR / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
SAMPLE_DATA_FILE = PROJECT_DIR / "sample_telco_churn_data.csv"
NUMERIC_FEATURES = ["tenure", "MonthlyCharges"]
CATEGORICAL_FEATURES = [
    "Contract",
    "InternetService",
    "PaymentMethod",
    "TechSupport",
]
MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


@st.cache_data
def load_data():
    if MAIN_DATA_FILE.exists():
        data_file = MAIN_DATA_FILE
        using_sample = False
    elif SAMPLE_DATA_FILE.exists():
        data_file = SAMPLE_DATA_FILE
        using_sample = True
    else:
        raise FileNotFoundError(
            "Could not find WA_Fn-UseC_-Telco-Customer-Churn.csv or "
            "sample_telco_churn_data.csv in the project folder."
        )

    data = pd.read_csv(data_file)
    for column in data.select_dtypes(exclude="number").columns:
        data[column] = data[column].str.strip()

    data["TotalCharges"] = pd.to_numeric(data["TotalCharges"], errors="coerce")
    zero_tenure = data["tenure"].eq(0)
    data.loc[zero_tenure, "TotalCharges"] = 0
    data = data.dropna().drop_duplicates().copy()

    senior_citizen = pd.to_numeric(data["SeniorCitizen"], errors="coerce")
    data["SeniorCitizen"] = senior_citizen.map({0: "No", 1: "Yes"})
    data["ChurnFlag"] = data["Churn"].map({"Yes": 1, "No": 0})
    data["TenureGroup"] = pd.cut(
        data["tenure"],
        bins=[-1, 12, 24, 48, 72],
        labels=["0-12", "13-24", "25-48", "49-72"],
    )
    data = data.dropna(subset=["SeniorCitizen", "ChurnFlag", "TenureGroup"]).copy()
    return data, data_file.name, using_sample


@st.cache_resource
def train_model(data):
    features = data[MODEL_FEATURES]
    target = data["ChurnFlag"]
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        stratify=target,
        random_state=42,
    )

    preprocessing = ColumnTransformer(
        transformers=[
            ("numbers", StandardScaler(), NUMERIC_FEATURES),
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    scores = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
    }
    return pipeline, scores


try:
    data, data_source, using_sample = load_data()
except (FileNotFoundError, KeyError, pd.errors.ParserError) as error:
    st.error(f"Could not load the customer dataset: {error}")
    st.stop()

if using_sample:
    st.warning("Using SAMPLE data. Results are not real.")

st.markdown(
    f"""
    <section class="hero">
      <div class="hero-copy">
        <p class="hero-eyebrow">Customer intelligence · Retention analytics</p>
        <h1>Customer Churn Dashboard</h1>
        <p class="hero-subtitle">Understand the patterns behind customer loyalty and churn.</p>
      </div>
      <div class="hero-source"><span class="source-dot"></span>{data_source}</div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="padding: 1.2rem .2rem 1.4rem;">
      <div style="font: 800 1.25rem Manrope,sans-serif;letter-spacing:-.04em;color:#fff;">
        northstar<span style="color:#aa9eff">.</span>
      </div>
      <div style="margin-top:.35rem;color:#929db2;font-size:.74rem;">Customer retention studio</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    '<p style="color:#b7adff;font-size:.68rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;">Dashboard filter</p>',
    unsafe_allow_html=True,
)
contract_filter = st.sidebar.selectbox(
    "Contract",
    ["All", "Month-to-month", "One year", "Two year"],
)

if contract_filter == "All":
    filtered_data = data
else:
    filtered_data = data.loc[data["Contract"] == contract_filter]

if filtered_data.empty:
    st.warning("No customers match this contract filter.")
else:
    total_customers = len(filtered_data)
    churned_customers = int(filtered_data["ChurnFlag"].sum())
    churn_rate = filtered_data["ChurnFlag"].mean() * 100
    average_monthly_charge = filtered_data["MonthlyCharges"].mean()

    metric_columns = st.columns(4)
    metric_columns[0].metric("Total Customers", f"{total_customers:,}")
    metric_columns[1].metric("Churned Customers", f"{churned_customers:,}")
    metric_columns[2].metric("Churn Rate (%)", f"{churn_rate:.2f}%")
    metric_columns[3].metric(
        "Average Monthly Charge",
        f"${average_monthly_charge:,.2f}",
    )

    chart_columns = st.columns(3)

    churn_counts = filtered_data["Churn"].value_counts()
    retained_count = int(churn_counts.get("No", 0))
    churned_count = int(churn_counts.get("Yes", 0))
    with chart_columns[0].container(border=True):
        st.markdown("#### Customer mix")
        st.caption("Retained and churned customers")
        pie_figure, pie_axis = plt.subplots(figsize=(4.2, 3.2), facecolor="white")
        pie_axis.pie(
            [retained_count, churned_count],
            labels=["Retained", "Churned"],
            colors=["#4c78a8", "#e4572e"],
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=.72,
            textprops={"color": "#3e4a60", "fontsize": 9},
            wedgeprops={"linewidth": 2, "edgecolor": "white"},
        )
        pie_axis.axis("equal")
        chart_columns[0].pyplot(pie_figure, width="stretch")
    plt.close(pie_figure)

    contract_summary = (
        filtered_data.groupby("Contract", observed=True)["ChurnFlag"]
        .mean()
        .mul(100)
        .reset_index(name="Churn rate (%)")
    )
    with chart_columns[1].container(border=True):
        st.markdown("#### Contract patterns")
        st.caption("Churn rate across contract types")
        contract_figure, contract_axis = plt.subplots(figsize=(4.2, 3.2), facecolor="white")
        sns.barplot(
            data=contract_summary,
            x="Contract",
            y="Churn rate (%)",
            color="#766bd8",
            ax=contract_axis,
        )
        contract_axis.set_xlabel("Contract", color="#788398", fontsize=9)
        contract_axis.set_ylabel("Churn rate (%)", color="#788398", fontsize=9)
        contract_axis.tick_params(axis="x", rotation=18, labelsize=8, colors="#59657a")
        contract_axis.tick_params(axis="y", labelsize=8, colors="#59657a")
        contract_axis.set_ylim(0, max(10, float(contract_summary["Churn rate (%)"].max()) * 1.18))
        contract_axis.grid(axis="y", color="#e9edf4", linewidth=.8)
        contract_axis.set_axisbelow(True)
        contract_axis.spines[["top", "right", "left"]].set_visible(False)
        contract_axis.spines["bottom"].set_color("#e3e7ef")
        contract_figure.tight_layout(pad=1.2)
        chart_columns[1].pyplot(contract_figure, width="stretch")
    plt.close(contract_figure)

    tenure_summary = (
        filtered_data.groupby("TenureGroup", observed=True)["ChurnFlag"]
        .mean()
        .mul(100)
        .reset_index(name="Churn rate (%)")
    )
    with chart_columns[2].container(border=True):
        st.markdown("#### Tenure patterns")
        st.caption("Churn rate across customer lifecycle")
        tenure_figure, tenure_axis = plt.subplots(figsize=(4.2, 3.2), facecolor="white")
        sns.barplot(
            data=tenure_summary,
            x="TenureGroup",
            y="Churn rate (%)",
            color="#4c78a8",
            ax=tenure_axis,
        )
        tenure_axis.set_xlabel("Tenure group (months)", color="#788398", fontsize=9)
        tenure_axis.set_ylabel("Churn rate (%)", color="#788398", fontsize=9)
        tenure_axis.tick_params(axis="x", labelsize=8, colors="#59657a")
        tenure_axis.tick_params(axis="y", labelsize=8, colors="#59657a")
        tenure_axis.set_ylim(0, max(10, float(tenure_summary["Churn rate (%)"].max()) * 1.18))
        tenure_axis.grid(axis="y", color="#e9edf4", linewidth=.8)
        tenure_axis.set_axisbelow(True)
        tenure_axis.spines[["top", "right", "left"]].set_visible(False)
        tenure_axis.spines["bottom"].set_color("#e3e7ef")
        tenure_figure.tight_layout(pad=1.2)
        chart_columns[2].pyplot(tenure_figure, width="stretch")
    plt.close(tenure_figure)

st.markdown('<p class="section-kicker">Prediction workspace</p>', unsafe_allow_html=True)
st.header("Predict customer churn")
st.markdown(
    '<p class="section-note">Adjust the customer profile to estimate churn risk and reveal practical retention ideas.</p>',
    unsafe_allow_html=True,
)

try:
    model, model_scores = train_model(data)
except ValueError as error:
    st.error(f"Could not train the churn prediction model: {error}")
    st.stop()

with st.form("prediction_form"):
    st.markdown("**Customer profile**")
    input_columns = st.columns(3)
    contract = input_columns[0].selectbox(
        "Contract",
        ["Month-to-month", "One year", "Two year"],
    )
    tenure = input_columns[1].slider(
        "Tenure in months",
        min_value=0,
        max_value=72,
        value=int(data["tenure"].median()),
    )
    monthly_charges = input_columns[2].number_input(
        "Monthly charges",
        min_value=0.0,
        max_value=float(data["MonthlyCharges"].max()),
        value=float(data["MonthlyCharges"].mean()),
        step=1.0,
    )
    internet_service = input_columns[0].selectbox(
        "Internet service",
        sorted(data["InternetService"].unique()),
    )
    payment_method = input_columns[1].selectbox(
        "Payment method",
        sorted(data["PaymentMethod"].unique()),
    )
    tech_support = input_columns[2].selectbox(
        "Tech support",
        ["Yes", "No", "No internet service"],
    )
    predict_clicked = st.form_submit_button("Predict")

if predict_clicked:
    customer = pd.DataFrame(
        [
            {
                "Contract": contract,
                "tenure": tenure,
                "MonthlyCharges": monthly_charges,
                "InternetService": internet_service,
                "PaymentMethod": payment_method,
                "TechSupport": tech_support,
            }
        ],
        columns=MODEL_FEATURES,
    )
    probability = float(model.predict_proba(customer)[0, 1]) * 100
    if probability < 35:
        risk_label = "Low"
        risk_color = "green"
    elif probability < 60:
        risk_label = "Medium"
        risk_color = "orange"
    else:
        risk_label = "High"
        risk_color = "red"

    st.markdown(
        f"""
        <div class="risk-result {risk_label.lower()}">
          <p class="risk-label">Estimated churn probability</p>
          <p class="risk-value">{probability:.1f}% <span style="color:{'#42a77a' if risk_label == 'Low' else '#e3a23d' if risk_label == 'Medium' else '#dd5b5b'}">{risk_label} risk</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    retention_tips = [
        "Offer a discounted annual plan."
        if contract == "Month-to-month"
        else "Offer a renewal benefit before the current contract ends.",
        "Offer a tech-support plan or a personal setup session."
        if tech_support == "No"
        else "Schedule a proactive check-in about the customer's support experience.",
        "Provide an onboarding check-in and early loyalty offer."
        if tenure <= 12
        else "Recognize the customer's tenure with a personalized loyalty benefit.",
    ]

    st.markdown('<p class="retention-heading">Suggested retention ideas</p>', unsafe_allow_html=True)
    for tip in retention_tips[:3]:
        st.markdown(f"- {tip}")

with st.expander("Model performance"):
    score_columns = st.columns(3)
    score_columns[0].metric("Test accuracy", f"{model_scores['accuracy']:.2%}")
    score_columns[1].metric("Test precision", f"{model_scores['precision']:.2%}")
    score_columns[2].metric("Test recall", f"{model_scores['recall']:.2%}")
    st.caption(
        "Recall matters more than accuracy because far fewer customers churn than stay."
    )

st.divider()
st.markdown(
    '<div class="app-footer">Association in the data does not prove causation.</div>',
    unsafe_allow_html=True,
)
