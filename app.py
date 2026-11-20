"""Дашборд успішності студентів університету (Streamlit).

Запуск:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Успішність студентів", page_icon="🎓", layout="wide")

REQUIRED = {"student_id", "student", "group", "semester", "subject", "grade"}


@st.cache_data
def load_data(source) -> pd.DataFrame:
    """Читає CSV і перевіряє наявність потрібних колонок."""
    df = pd.read_csv(source)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"У CSV відсутні колонки: {', '.join(sorted(missing))}")
    df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
    return df.dropna(subset=["grade"])


# ---------- Завантаження даних ----------
st.title("🎓 Дашборд успішності студентів")

uploaded = st.sidebar.file_uploader("Завантажити свій CSV", type="csv")
try:
    data = load_data(uploaded if uploaded else "students.csv")
except Exception as e:
    st.error(f"Не вдалося завантажити дані: {e}")
    st.stop()

# ---------- Фільтри ----------
st.sidebar.header("Фільтри")
groups = st.sidebar.multiselect("Група", sorted(data["group"].unique()), default=sorted(data["group"].unique()))
subjects = st.sidebar.multiselect("Предмет", sorted(data["subject"].unique()), default=sorted(data["subject"].unique()))
semesters = st.sidebar.multiselect("Семестр", sorted(data["semester"].unique()), default=sorted(data["semester"].unique()))

df = data[data["group"].isin(groups) & data["subject"].isin(subjects) & data["semester"].isin(semesters)]

if df.empty:
    st.warning("За обраними фільтрами даних немає. Змініть параметри.")
    st.stop()

# ---------- Показники ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Студентів", df["student_id"].nunique())
c2.metric("Середня оцінка", f"{df['grade'].mean():.1f}")
c3.metric("Медіана", f"{df['grade'].median():.0f}")
c4.metric("Успішність (≥60)", f"{(df['grade'] >= 60).mean() * 100:.1f}%")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Середні оцінки", "📈 Динаміка", "🔗 Кореляції", "🗂 Дані"])

# ---------- Вкладка 1: середні оцінки ----------
with tab1:
    left, right = st.columns(2)

    by_subject = df.groupby("subject", as_index=False)["grade"].mean().sort_values("grade")
    fig = px.bar(by_subject, x="grade", y="subject", orientation="h", text_auto=".1f",
                 title="Середня оцінка за предметами", labels={"grade": "Середня оцінка", "subject": "Предмет"})
    fig.update_xaxes(range=[0, 100])
    left.plotly_chart(fig, width="stretch")

    by_group = df.groupby("group", as_index=False)["grade"].mean()
    fig = px.bar(by_group, x="group", y="grade", text_auto=".1f", color="group",
                 title="Середня оцінка за групами", labels={"grade": "Середня оцінка", "group": "Група"})
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(showlegend=False)
    right.plotly_chart(fig, width="stretch")

    pivot = df.pivot_table(index="group", columns="subject", values="grade", aggfunc="mean")
    fig = px.imshow(pivot, text_auto=".1f", aspect="auto", color_continuous_scale="RdYlGn",
                    title="Середня оцінка: група × предмет")
    st.plotly_chart(fig, width="stretch")

    fig = px.histogram(df, x="grade", nbins=20, title="Розподіл оцінок", labels={"grade": "Оцінка"})
    st.plotly_chart(fig, width="stretch")

# ---------- Вкладка 2: динаміка ----------
with tab2:
    trend = df.groupby(["semester", "subject"], as_index=False)["grade"].mean()
    fig = px.line(trend, x="semester", y="grade", color="subject", markers=True,
                  title="Динаміка середньої оцінки за семестрами",
                  labels={"grade": "Середня оцінка", "semester": "Семестр", "subject": "Предмет"})
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, width="stretch")

# ---------- Вкладка 3: кореляції ----------
with tab3:
    st.subheader("Кореляція між предметами")
    st.caption("Для кожного студента береться середня оцінка з предмета (за обраними фільтрами); "
               "далі рахується коефіцієнт кореляції Пірсона між предметами.")

    student_subject = df.pivot_table(index="student_id", columns="subject", values="grade", aggfunc="mean")
    student_subject = student_subject.dropna(axis=1, how="all")

    if student_subject.shape[1] < 2 or student_subject.shape[0] < 3:
        st.info("Для аналізу кореляцій оберіть щонайменше 2 предмети та 3 студентів.")
    else:
        corr = student_subject.corr()
        fig = px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                        title="Матриця кореляцій (Пірсон)")
        st.plotly_chart(fig, width="stretch")

        # усі унікальні пари предметів (без діагоналі та дублікатів)
        cols = list(corr.columns)
        pairs = pd.DataFrame(
            [(cols[i], cols[j], corr.iloc[i, j]) for i in range(len(cols)) for j in range(i + 1, len(cols))],
            columns=["Предмет 1", "Предмет 2", "Кореляція"],
        ).sort_values("Кореляція", ascending=False).reset_index(drop=True)
        pairs["Кореляція"] = pairs["Кореляція"].round(3)

        a, b = st.columns(2)
        a.markdown("**Найсильніший зв’язок**")
        a.dataframe(pairs.head(3), hide_index=True, width="stretch")
        b.markdown("**Найслабший зв’язок**")
        b.dataframe(pairs.tail(3).iloc[::-1], hide_index=True, width="stretch")

        st.markdown("**Діаграма розсіювання для двох предметів**")
        s1, s2 = st.columns(2)
        subj_list = list(student_subject.columns)
        x_subj = s1.selectbox("Вісь X", subj_list, index=0)
        y_subj = s2.selectbox("Вісь Y", subj_list, index=min(1, len(subj_list) - 1))
        fig = px.scatter(student_subject.reset_index(), x=x_subj, y=y_subj, trendline="ols",
                         title=f"{x_subj} ↔ {y_subj}")
        st.plotly_chart(fig, width="stretch")

# ---------- Вкладка 4: дані ----------
with tab4:
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button("⬇️ Завантажити відфільтровані дані (CSV)",
                       df.to_csv(index=False).encode("utf-8"), "filtered_students.csv", "text/csv")
