import pandas as pd
import scipy.stats as stats
import streamlit as st
import plotly.express as px


users = pd.read_excel('dannye-dlia-keisa-po-pa-cebbefc3-5b29-4f88-b6d4-3336c88d743f.xlsx', sheet_name="Пользователи")
payments = pd.read_excel('dannye-dlia-keisa-po-pa-cebbefc3-5b29-4f88-b6d4-3336c88d743f.xlsx', sheet_name="Платежи")

def prepare_user_data(users: pd.DataFrame) -> pd.DataFrame:
    users = users.dropna(subset=["user_id", "group"])
    users = users.drop_duplicates(subset=["user_id"])
    users = users[(users["age"] >= 18) & (users["age"] <= 80)]

    return users

def prepare_payment_data(payments: pd.DataFrame) -> pd.DataFrame:
    payments = payments.dropna(subset=["payment_id", "user_id", "group", "step1_opened"])
    payments = payments.drop_duplicates(subset=["payment_id", "user_id"])

    return payments

def users_metrics(users: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    count_by_groups = users.groupby("group")["user_id"].count().reset_index().rename(columns={"user_id": "count"})
    count_by_cities = users.groupby("city")["user_id"].count().reset_index().rename(columns={"user_id": "count"})
    count_by_ages = users.groupby("age")["user_id"].count().reset_index().rename(columns={"user_id": "count"})
    count_by_device_types = users.groupby("device_type")["user_id"].count().reset_index().rename(columns={"user_id": "count"})

    return count_by_groups, count_by_cities, count_by_ages, count_by_device_types

def payments_metrics(users: pd.DataFrame, payments: pd.DataFrame):
    merged_data = pd.merge(users, payments, on="user_id", suffixes=("_user", "_payment"))

    group_A = merged_data[merged_data["group_user"] == "A"]
    group_B = merged_data[merged_data["group_user"] == "B"]

    success_A = group_A[(group_A["step4_success"].notnull()) & (group_A["step3_confirmed"].notnull()) & (group_A["step2_entered"].notnull()) & (group_A["step1_opened"].notnull())].drop_duplicates(subset=["user_id"])
    success_B = group_B[(group_B["step4_success"].notnull()) & (group_B["step3_confirmed"].notnull()) & (group_B["step2_entered"].notnull()) & (group_B["step1_opened"].notnull())].drop_duplicates(subset=["user_id"])

    failed_A = group_A[~group_A["user_id"].isin(success_A["user_id"])].drop_duplicates(subset=["user_id"])
    failed_B = group_B[~group_B["user_id"].isin(success_B["user_id"])].drop_duplicates(subset=["user_id"])

    return success_A["user_id"].nunique(), success_B["user_id"].nunique(), failed_A["user_id"].nunique(), failed_B["user_id"].nunique()

def calc_conversion(users: pd.DataFrame, payments: pd.DataFrame) -> tuple[float, float]:
    merged_data = pd.merge(users, payments, on="user_id", suffixes=("_user", "_payment"))
    
    group_A = merged_data[merged_data["group_user"] == "A"]
    group_B = merged_data[merged_data["group_user"] == "B"]

    success_A = group_A[(group_A["step4_success"].notnull()) & (group_A["step3_confirmed"].notnull()) & (group_A["step2_entered"].notnull()) & (group_A["step1_opened"].notnull())]
    success_B = group_B[(group_B["step4_success"].notnull()) & (group_B["step3_confirmed"].notnull()) & (group_B["step2_entered"].notnull()) & (group_B["step1_opened"].notnull())]

    conversion_A = round((success_A["user_id"].nunique() / group_A["user_id"].nunique()), 5)
    conversion_B = round((success_B["user_id"].nunique() / group_B["user_id"].nunique()), 5)

    return conversion_A, conversion_B

def chart_success_by_age_and_device(users: pd.DataFrame, payments: pd.DataFrame):
    merged_data = pd.merge(users, payments, on="user_id", suffixes=("_user", "_payment"))

    success = merged_data[(merged_data["step4_success"].notnull()) & (merged_data["step3_confirmed"].notnull()) & (merged_data["step2_entered"].notnull()) & (merged_data["step1_opened"].notnull())].drop_duplicates(subset=["user_id"])

    merged_data["age_group"] = pd.cut(
        merged_data["age"],
        bins=[17, 30, 50, 80],
        labels=["18-30", "31-50", "51-80"]
    )
    success["age_group"] = pd.cut(
        success["age"],
        bins=[17, 30, 50, 80],
        labels=["18-30", "31-50", "51-80"]
    )

    total_age = merged_data.groupby(["age_group", "group_user"])["user_id"].nunique().reset_index().rename(columns={"user_id": "total_count"})
    success_age = success.groupby(["age_group","group_user"])["user_id"].nunique().reset_index().rename(columns={"user_id": "success_count"})
    age_stats = pd.merge(
        total_age,
        success_age,
        on=["age_group", "group_user"]
    )
    age_stats["conversion"] = round((age_stats["success_count"] / age_stats["total_count"]) * 100, 2)

    total_device = merged_data.groupby(["device_type", "group_user"])["user_id"].nunique().reset_index().rename(columns={"user_id": "total_count"})
    success_device = success.groupby(["device_type","group_user"])["user_id"].nunique().reset_index().rename(columns={"user_id": "success_count"})
    device_stats = pd.merge(
        total_device,
        success_device,
        on=["device_type", "group_user"]
    )
    device_stats["conversion"] = round((device_stats["success_count"] / device_stats["total_count"]) * 100, 2)

    fig = px.bar(
        age_stats, 
        x="age_group", 
        y="conversion", 
        title="Конверсия по возрасту"   , 
        labels={"age_group": "Возраст", "conversion": "Конверсия, %"}, 
        barmode="group", 
        color="group_user",
        text="conversion"
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig)

    fig = px.bar(
        device_stats, 
        x="device_type", 
        y="conversion", 
        title="Конверсия по устройствам"   , 
        labels={"device_type": "Устройство", "conversion": "Конверсия, %"}, 
        barmode="group",
        color="group_user",
        text="conversion"
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig)

def run_pipeline(users: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    users = prepare_user_data(users)
    payments = prepare_payment_data(payments)

    success_A, success_B, failed_A, failed_B = payments_metrics(users, payments)
    conversion_A, conversion_B = calc_conversion(users, payments)

    result = stats.chi2_contingency([[success_A, failed_A], [success_B, failed_B]])

    print(f"Результат хи-квадрат теста: {result[0]:.5f}, p-value: {result[1]:.12f}")
    print(f"Конверсия группы A: {conversion_A*100}; Конверсия группы B: {conversion_B*100}")

    chart_success_by_age_and_device(users, payments)


run_pipeline(users, payments)
