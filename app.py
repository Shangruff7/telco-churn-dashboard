import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from databricks import sql
import os

st.set_page_config(
    page_title="Telco Churn Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: Arial, sans-serif; }
.stApp { background-color: #0a0e1a; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1225 0%, #111827 100%);
    border-right: 1px solid #1e2d4a;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi-card.blue::before    { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
.kpi-card.red::before     { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-card.amber::before   { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-card.emerald::before { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-card.violet::before  { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.kpi-label {
    font-family: Arial, sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-value {
    font-family: Arial, sans-serif;
    font-size: 26px;
    font-weight: 700;
    color: #f1f5f9;
    line-height: 1;
    white-space: nowrap;
}
.kpi-delta {
    font-family: Arial, sans-serif;
    font-size: 9px;
    margin-top: 4px;
    color: #64748b;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.section-header {
    font-family: Arial, sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3b82f6;
    margin: 28px 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2d4a;
}
.stTabs [data-baseweb="tab-list"] {
    background: #0d1225;
    border-bottom: 1px solid #1e2d4a;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    font-family: Arial, sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 24px;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #f1f5f9 !important;
    border-bottom: 2px solid #3b82f6 !important;
    background: rgba(0,0,0,0) !important;
}
.modern-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.modern-table th {
    background: #0d1225;
    color: #64748b;
    font-family: Arial, sans-serif;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 12px 16px;
    border-bottom: 1px solid #1e2d4a;
    text-align: left;
}
.modern-table td {
    font-family: Arial, sans-serif;
    font-size: 12px;
    padding: 11px 16px;
    color: #cbd5e1;
    border-bottom: 1px solid #111827;
}
.modern-table tr:hover td { background: #111827; }
.pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.pill-red   { background: #2d1a1a; color: #f87171; }
.pill-green { background: #1a2d1a; color: #34d399; }
.pill-amber { background: #2d251a; color: #fbbf24; }
.bar-bg   { background: #1e2d4a; border-radius: 4px; height: 6px; width: 100%; }
.bar-fill { height: 6px; border-radius: 4px; background: linear-gradient(90deg, #3b82f6, #60a5fa); }
h1, h2, h3 { color: #f1f5f9 !important; font-family: Arial, sans-serif !important; }
</style>
""", unsafe_allow_html=True)

# ── Connection ────────────────────────────────────────────────
DATABRICKS_HOST = "dbc-a11fb796-04ab.cloud.databricks.com"
HTTP_PATH       = "/sql/1.0/warehouses/1af7885e514fcf3e"
TOKEN           = os.environ.get("DATABRICKS_TOKEN")

@st.cache_data(ttl=3600)
def load_data():
    try:
        with sql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=HTTP_PATH,
            access_token=TOKEN,
            _tls_no_verify=True
        ) as conn:
            def q(query):
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description]
                    return pd.DataFrame(rows, columns=cols)
            raw = q("""
                SELECT customerID, gender, SeniorCitizen, Partner, Dependents,
                       tenure, PhoneService, MultipleLines, InternetService,
                       OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport,
                       StreamingTV, StreamingMovies, Contract, PaperlessBilling,
                       PaymentMethod, MonthlyCharges, TotalCharges, Churn
                FROM default.telco_silver
            """)
            return raw
    except Exception as e:
        st.error(f"Connection error: {type(e).__name__}: {str(e)}")
        st.stop()

raw = load_data()

# ── Sidebar Filters ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filters")
    st.markdown("---")
    sel_contract = st.multiselect("Contract Type",    options=raw["Contract"].unique().tolist(),        default=raw["Contract"].unique().tolist())
    sel_internet = st.multiselect("Internet Service", options=raw["InternetService"].unique().tolist(), default=raw["InternetService"].unique().tolist())
    sel_senior   = st.multiselect("Senior Citizen",   options=["Senior","Non-Senior"],                  default=["Senior","Non-Senior"])
    sel_payment  = st.multiselect("Payment Method",   options=raw["PaymentMethod"].unique().tolist(),   default=raw["PaymentMethod"].unique().tolist())
    st.markdown("---")
    st.markdown("<p style='font-size:9px;color:#334155;text-align:center'>Telco Churn Intelligence<br>Databricks · Delta Lake · PySpark</p>", unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────
senior_vals = [{"Senior":1,"Non-Senior":0}[s] for s in sel_senior]
filtered = raw[
    raw["Contract"].isin(sel_contract) &
    raw["InternetService"].isin(sel_internet) &
    raw["SeniorCitizen"].isin(senior_vals) &
    raw["PaymentMethod"].isin(sel_payment)
]

# ── KPIs ──────────────────────────────────────────────────────
total_cust  = len(filtered)
total_churn = (filtered["Churn"]=="Yes").sum()
churn_rate  = round(total_churn/total_cust*100,2) if total_cust>0 else 0
rev_at_risk = round(filtered[filtered["Churn"]=="Yes"]["MonthlyCharges"].sum(),0)
avg_tenure  = round(filtered["tenure"].mean(),1)

# ── Header ────────────────────────────────────────────────────
st.markdown(f"""
<div style='padding:8px 0 20px 0'>
    <p style='font-size:11px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:#3b82f6;margin:0;font-family:Arial'>
        DATABRICKS · DELTA LAKE · PYSPARK
    </p>
    <h1 style='font-size:32px;font-weight:700;margin:4px 0;color:#f1f5f9;font-family:Arial'>
        Telco Churn Intelligence
    </h1>
    <p style='color:#475569;font-size:11px;margin:0;font-family:Arial'>
        Customer retention analytics across {total_cust:,} customers · Medallion Architecture
    </p>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────
k1,k2,k3,k4,k5 = st.columns(5)
with k1:
    st.markdown(f"<div class='kpi-card blue'><div class='kpi-label'>Total Customers</div><div class='kpi-value'>{total_cust:,}</div><div class='kpi-delta'>Active subscribers</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card red'><div class='kpi-label'>Churned</div><div class='kpi-value'>{total_churn:,}</div><div class='kpi-delta'>Lost customers</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card amber'><div class='kpi-label'>Churn Rate</div><div class='kpi-value'>{churn_rate}%</div><div class='kpi-delta'>Of total base</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-card emerald'><div class='kpi-label'>Revenue at Risk</div><div class='kpi-value'>${rev_at_risk:,.0f}</div><div class='kpi-delta'>Monthly exposure</div></div>", unsafe_allow_html=True)
with k5:
    st.markdown(f"<div class='kpi-card violet'><div class='kpi-label'>Avg Tenure</div><div class='kpi-value'>{avg_tenure}</div><div class='kpi-delta'>Months retained</div></div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

# ── Plot defaults ─────────────────────────────────────────────
PLOT_BG = PAPER_BG = "#0a0e1a"

def base_layout(title="", height=320):
    return dict(
        title=dict(text=title, font=dict(color="#f1f5f9", size=13, family="Arial"), x=0, xanchor="left"),
        plot_bgcolor=PLOT_BG, paper_bgcolor=PAPER_BG,
        font=dict(color="#94a3b8", family="Arial", size=11),
        margin=dict(l=16, r=16, t=44, b=16),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8", size=10)),
        xaxis=dict(gridcolor="#1e2d4a", zerolinecolor="#1e2d4a", tickfont=dict(color="#64748b", size=10)),
        yaxis=dict(gridcolor="#1e2d4a", zerolinecolor="#1e2d4a", tickfont=dict(color="#64748b", size=10)),
    )

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📊  Analytics Dashboard", "🔍  Cross-Tab Explorer"])

# ════════════════════════════════════════════════════════
# TAB 1
# ════════════════════════════════════════════════════════
with tab1:

    r1c1, r1c2, r1c3 = st.columns([1.2, 1, 1.8])

    with r1c1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=churn_rate,
            delta={"reference":20,"valueformat":".1f","suffix":"%",
                   "increasing":{"color":"#ef4444"},"decreasing":{"color":"#10b981"}},
            number={"suffix":"%","font":{"size":40,"color":"#f1f5f9","family":"Arial"}},
            title={"text":"CHURN RATE","font":{"size":10,"color":"#64748b","family":"Arial"}},
            gauge={
                "axis":{"range":[0,60],"tickwidth":1,"tickcolor":"#1e2d4a",
                        "tickfont":{"color":"#475569","size":9}},
                "bar":{"color":"#3b82f6","thickness":0.25},
                "bgcolor":"#0d1225","borderwidth":0,
                "steps":[
                    {"range":[0,15],"color":"#0d2010"},
                    {"range":[15,30],"color":"#1a2510"},
                    {"range":[30,45],"color":"#2d1f0a"},
                    {"range":[45,60],"color":"#2d0f0f"},
                ],
                "threshold":{"line":{"color":"#ef4444","width":2},"thickness":0.75,"value":26.5}
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
            height=260, margin=dict(l=20,r=20,t=40,b=0),
            font=dict(family="Arial")
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with r1c2:
        phone_f = filtered.groupby("PhoneService").agg(total=("customerID","count")).reset_index()
        fig_donut = go.Figure(go.Pie(
            labels=phone_f["PhoneService"],
            values=phone_f["total"],
            hole=0.65,
            marker=dict(colors=["#3b82f6","#1e3a5f"], line=dict(color=PLOT_BG, width=3)),
            textfont=dict(color="#94a3b8", size=10),
            hovertemplate="<b>%{label}</b><br>Customers: %{value:,}<br>Share: %{percent}<extra></extra>"
        ))
        fig_donut.add_annotation(
            text=f"<b>{phone_f['total'].sum():,}</b><br>customers",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#f1f5f9", family="Arial"),
            align="center"
        )
        fig_donut.update_layout(**base_layout("Phone Service Split", height=260))
        st.plotly_chart(fig_donut, use_container_width=True)

    with r1c3:
        rev_f = filtered.groupby("Contract").apply(
            lambda g: pd.Series({
                "revenue_at_risk":  g.loc[g["Churn"]=="Yes","MonthlyCharges"].sum(),
                "revenue_retained": g.loc[g["Churn"]=="No","MonthlyCharges"].sum()
            })
        ).reset_index()
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(
            name="Retained", x=rev_f["Contract"], y=rev_f["revenue_retained"],
            marker=dict(color="#10b981", opacity=0.85)
        ))
        fig_rev.add_trace(go.Bar(
            name="At Risk", x=rev_f["Contract"], y=rev_f["revenue_at_risk"],
            marker=dict(color="#ef4444", opacity=0.85)
        ))
        fig_rev.update_layout(
            **base_layout("Monthly Revenue — Retained vs At Risk", height=260),
            barmode="stack"
        )
        st.plotly_chart(fig_rev, use_container_width=True)

    st.markdown("<div class='section-header'>BREAKDOWN ANALYSIS</div>", unsafe_allow_html=True)
    r2c1, r2c2 = st.columns([1.3, 1])

    with r2c1:
        dim_options = {
            "Payment Method":    "PaymentMethod",
            "Internet Service":  "InternetService",
            "Contract Type":     "Contract",
            "Gender":            "gender",
            "Partner":           "Partner",
            "Dependents":        "Dependents",
            "Paperless Billing": "PaperlessBilling",
            "Multiple Lines":    "MultipleLines",
            "Tech Support":      "TechSupport",
            "Streaming TV":      "StreamingTV",
        }
        sel_dim = st.selectbox("Select Dimension", list(dim_options.keys()), index=0)
        dim_col = dim_options[sel_dim]

        dim_df = filtered.groupby(dim_col).agg(
            total=("customerID","count"),
            churned=("Churn", lambda x: (x=="Yes").sum())
        ).reset_index()
        dim_df["churn_rate_pct"] = round(dim_df["churned"]/dim_df["total"]*100,2)
        dim_df = dim_df.sort_values("churn_rate_pct", ascending=True)

        fig_hbar = go.Figure(go.Bar(
            y=dim_df[dim_col], x=dim_df["churn_rate_pct"],
            orientation="h",
            marker=dict(
                color=dim_df["churn_rate_pct"],
                colorscale=[[0,"#1e3a5f"],[0.5,"#3b82f6"],[1,"#ef4444"]],
                showscale=False
            ),
            text=[f"{v}%" for v in dim_df["churn_rate_pct"]],
            textposition="outside",
            textfont=dict(color="#94a3b8", size=10),
            customdata=dim_df["churned"],
            hovertemplate="<b>%{y}</b><br>Churn Rate: %{x}%<br>Churned: %{customdata:,}<extra></extra>"
        ))
        fig_hbar.update_layout(
            **base_layout(f"Churn Rate by {sel_dim}", height=320),
            xaxis_title="Churn Rate %", yaxis_title=""
        )
        st.plotly_chart(fig_hbar, use_container_width=True)

    with r2c2:
        ten_f = filtered.copy()
        ten_f["tenure_band"] = pd.cut(ten_f["tenure"], bins=[0,12,24,48,72],
                                       labels=["0-12 mo","13-24 mo","25-48 mo","49+ mo"])
        ten_agg = ten_f.groupby("tenure_band", observed=True).agg(
            total=("customerID","count"),
            churned=("Churn", lambda x: (x=="Yes").sum())
        ).reset_index()
        ten_agg["churn_rate_pct"] = round(ten_agg["churned"]/ten_agg["total"]*100,2)

        fig_tenure = go.Figure(go.Scatter(
            x=ten_agg["tenure_band"].astype(str),
            y=ten_agg["churn_rate_pct"],
            mode="lines+markers+text",
            line=dict(color="#3b82f6", width=2.5),
            marker=dict(size=8, color="#3b82f6", line=dict(color="#0a0e1a", width=2)),
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
            text=[f"{v}%" for v in ten_agg["churn_rate_pct"]],
            textposition="top center",
            textfont=dict(color="#94a3b8", size=10),
            hovertemplate="<b>%{x}</b><br>Churn: %{y}%<extra></extra>"
        ))
        fig_tenure.update_layout(**base_layout("Churn Rate by Tenure Band", height=320))
        st.plotly_chart(fig_tenure, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 2
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)

    dim_map = {
        "Contract Type":     "Contract",
        "Internet Service":  "InternetService",
        "Payment Method":    "PaymentMethod",
        "Gender":            "gender",
        "Senior Citizen":    "SeniorCitizen",
        "Partner":           "Partner",
        "Dependents":        "Dependents",
        "Paperless Billing": "PaperlessBilling",
        "Phone Service":     "PhoneService",
        "Tech Support":      "TechSupport",
        "Streaming TV":      "StreamingTV",
        "Online Security":   "OnlineSecurity",
    }

    ct1, ct2, ct3 = st.columns([1,1,2])
    with ct1:
        row_dim = st.selectbox("Row Dimension", list(dim_map.keys()), index=0)
    with ct2:
        col_dim = st.selectbox("Column Dimension", list(dim_map.keys()), index=1)
    with ct3:
        metric = st.radio("Metric", ["Churn Rate %","Churned Count","Total Customers"], horizontal=True)

    r_col = dim_map[row_dim]
    c_col = dim_map[col_dim]

    cross = filtered.groupby([r_col, c_col]).agg(
        total=("customerID","count"),
        churned=("Churn", lambda x: (x=="Yes").sum())
    ).reset_index()
    cross["churn_rate_pct"] = round(cross["churned"]/cross["total"]*100,1)

    if metric == "Churn Rate %":
        val_col="churn_rate_pct"; fmt=lambda v:f"{v}%"
        cscale=[[0,"#0d2010"],[0.4,"#1e3a5f"],[0.7,"#3b82f6"],[1,"#ef4444"]]
    elif metric == "Churned Count":
        val_col="churned"; fmt=lambda v:f"{int(v):,}"
        cscale=[[0,"#0d1225"],[1,"#ef4444"]]
    else:
        val_col="total"; fmt=lambda v:f"{int(v):,}"
        cscale=[[0,"#0d1225"],[1,"#3b82f6"]]

    pivot = cross.pivot(index=r_col, columns=c_col, values=val_col).fillna(0)
    if r_col=="SeniorCitizen": pivot.index   = pivot.index.map({0:"Non-Senior",1:"Senior"})
    if c_col=="SeniorCitizen": pivot.columns = pivot.columns.map({0:"Non-Senior",1:"Senior"})

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=[str(r) for r in pivot.index],
        colorscale=cscale,
        text=[[fmt(v) for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=12, color="#f1f5f9", family="Arial"),
        hovertemplate=f"<b>%{{y}} × %{{x}}</b><br>{metric}: %{{text}}<extra></extra>",
        showscale=True,
        colorbar=dict(tickfont=dict(color="#64748b",size=9), bgcolor=PAPER_BG, outlinewidth=0)
    ))
    fig_heat.update_layout(**base_layout(f"{metric} — {row_dim} × {col_dim}", height=400))
    fig_heat.update_xaxes(side="bottom", tickfont=dict(color="#94a3b8",size=10), gridcolor="rgba(0,0,0,0)")
    fig_heat.update_yaxes(tickfont=dict(color="#94a3b8",size=10), gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("<div class='section-header'>DETAILED BREAKDOWN</div>", unsafe_allow_html=True)

    table_df = cross.copy()
    if r_col=="SeniorCitizen": table_df[r_col]=table_df[r_col].map({0:"Non-Senior",1:"Senior"})
    if c_col=="SeniorCitizen": table_df[c_col]=table_df[c_col].map({0:"Non-Senior",1:"Senior"})
    table_df = table_df.sort_values("churn_rate_pct", ascending=False)

    def churn_pill(rate):
        if rate>=35:   return f"<span class='pill pill-red'>{rate}%</span>"
        elif rate>=20: return f"<span class='pill pill-amber'>{rate}%</span>"
        else:          return f"<span class='pill pill-green'>{rate}%</span>"

    def spark_bar(val, max_val):
        pct = int(val/max_val*100) if max_val>0 else 0
        return f"<div class='bar-bg'><div class='bar-fill' style='width:{pct}%'></div></div>"

    max_total = table_df["total"].max()
    rows_html = ""
    for _, row in table_df.iterrows():
        rows_html += f"""<tr>
            <td><b style='color:#f1f5f9'>{row[r_col]}</b></td>
            <td>{row[c_col]}</td>
            <td>{int(row['total']):,}<br>{spark_bar(row['total'],max_total)}</td>
            <td>{int(row['churned']):,}</td>
            <td>{churn_pill(row['churn_rate_pct'])}</td>
        </tr>"""

    st.markdown(f"""
    <table class='modern-table'>
        <thead><tr>
            <th>{row_dim}</th><th>{col_dim}</th>
            <th>Total Customers</th><th>Churned</th><th>Churn Rate</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>""", unsafe_allow_html=True)