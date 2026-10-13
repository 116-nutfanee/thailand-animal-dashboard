from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ตั้งค่าหน้าต่างเว็บ
st.set_page_config(
    page_title="Thailand Threatened Species Dashboard",
    page_icon="🐾",
    layout="wide",
)


# อ่านและทำความสะอาดข้อมูล
@st.cache_data
def load_data():
    # กำหนดตำแหน่งไฟล์อัตโนมัติตามโฟลเดอร์ที่ app.py สถิตอยู่
    data_path = Path(__file__).parent / "animal-red.csv"
    df = pd.read_csv(data_path)

    # ลบพื้นที่ว่างส่วนเกินในคอลัมน์ข้อความ
    text_cols = [
        "ประเภท",
        "กลุ่มสัตว์",
        "คำย่อ",
        "Status",
        "สถานภาพของชนิดพันธุ์",
        "ชื่อวิทยาศาสตร์",
        "ชื่อไทย",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # แทนที่ 'nan' ด้วยข้อความระบุว่าไม่มีชื่อไทย
    df["ชื่อไทย"] = df["ชื่อไทย"].replace("nan", "ไม่ระบุชื่อไทย")
    return df


df = load_data()

# ส่วนหัวของ Dashboard
st.title("🐾 Thailand Red Data Dashboard: สถานภาพชนิดพันธุ์สัตว์ในประเทศไทย")
st.markdown("วิเคราะห์ข้อมูลสถานภาพสัตว์ป่าและสัตว์น้ำตามระดับความเสี่ยงการสูญพันธุ์ (Thailand Red Data)")

# Sidebar Filter (Interactive Widgets)
st.sidebar.header("🔍 กรองข้อมูล (Filters)")

# Filter 1: ประเภท
type_list = ["ทั้งหมด"] + list(df["ประเภท"].unique())
selected_type = st.sidebar.selectbox("เลือกประเภทสัตว์", type_list)

# Filter 2: กลุ่มสัตว์
if selected_type != "ทั้งหมด":
    filtered_groups = df[df["ประเภท"] == selected_type]["กลุ่มสัตว์"].unique()
else:
    filtered_groups = df["กลุ่มสัตว์"].unique()

selected_group = st.sidebar.multiselect(
    "เลือกกลุ่มสัตว์",
    options=list(filtered_groups),
    default=list(filtered_groups),
)

# Filter 3: สถานภาพ
status_list = list(df["สถานภาพของชนิดพันธุ์"].unique())
selected_status = st.sidebar.multiselect(
    "เลือกสถานภาพชนิดพันธุ์", options=status_list, default=status_list
)

# ค้นหาด้วยชื่อ
search_term = st.sidebar.text_input("🔎 ค้นหาชื่อสัตว์ (ไทย/วิทยาศาสตร์)", "")

# ประมวลผลการกรองข้อมูล
df_filtered = df[
    (df["กลุ่มสัตว์"].isin(selected_group))
    & (df["สถานภาพของชนิดพันธุ์"].isin(selected_status))
]

if selected_type != "ทั้งหมด":
    df_filtered = df_filtered[df_filtered["ประเภท"] == selected_type]

if search_term:
    df_filtered = df_filtered[
        df_filtered["ชื่อไทย"].str.contains(search_term, case=False, na=False)
        | df_filtered["ชื่อวิทยาศาสตร์"].str.contains(
            search_term, case=False, na=False
        )
    ]

# แสดงผล KPI Metrics
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("จำนวนชนิดพันธุ์ทั้งหมด", f"{len(df_filtered):,} ชนิด")

with col2:
    threatened_count = len(
        df_filtered[df_filtered["คำย่อ"].isin(["EX", "EW", "CR", "EN", "VU"])]
    )
    st.metric("ชนิดพันธุ์ที่เสี่ยง/สูญพันธุ์", f"{threatened_count:,} ชนิด")

with col3:
    st.metric("จำนวนกลุ่มสัตว์ที่พบ", f"{df_filtered['กลุ่มสัตว์'].nunique()} กลุ่ม")

with col4:
    st.metric("ข้อมูลไม่เพียงพอ (DD)", f"{len(df_filtered[df_filtered['คำย่อ'] == 'DD']):,} ชนิด")

st.markdown("---")

# การแสดงผลกราฟ (Data Visualization)
col_graph1, col_graph2 = st.columns(2)

with col_graph1:
    st.subheader("📊 สัดส่วนตามสถานภาพชนิดพันธุ์")
    status_counts = df_filtered["สถานภาพของชนิดพันธุ์"].value_counts().reset_index()
    status_counts.columns = ["สถานภาพ", "จำนวน"]

    fig1 = px.pie(
        status_counts,
        names="สถานภาพ",
        values="จำนวน",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig1, use_container_width=True)

with col_graph2:
    st.subheader("📈 จำนวนชนิดพันธุ์แบ่งตามกลุ่มสัตว์และสถานภาพ")
    group_status = (
        df_filtered.groupby(["กลุ่มสัตว์", "สถานภาพของชนิดพันธุ์"])
        .size()
        .reset_index(name="จำนวน")
    )

    fig2 = px.bar(
        group_status,
        x="กลุ่มสัตว์",
        y="จำนวน",
        color="สถานภาพของชนิดพันธุ์",
        barmode="stack",
        text_auto=True,
    )
    fig2.update_layout(xaxis_title="กลุ่มสัตว์", yaxis_title="จำนวนชนิดพันธุ์")
    st.plotly_chart(fig2, use_container_width=True)

# ตารางข้อมูล
st.subheader("📋 รายการข้อมูลชนิดพันธุ์สัตว์")
st.dataframe(
    df_filtered[
        [
            "ลำดับที่",
            "ประเภท",
            "กลุ่มสัตว์",
            "ชื่อไทย",
            "ชื่อวิทยาศาสตร์",
            "คำย่อ",
            "สถานภาพของชนิดพันธุ์",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)