import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Bruno Bot Dashboard")

df = pd.read_csv("trades.csv")

wins = (df.result == "GAIN").sum()
loss = (df.result == "LOSS").sum()

st.metric("Trades", len(df))
st.metric("Win rate", f"{wins/(wins+loss)*100:.1f}%")

df["R"] = df.result.map({"GAIN": 2, "LOSS": -1})
df["equity"] = df.R.cumsum()

fig = px.line(df, y="equity", title="Equity Curve")
st.plotly_chart(fig)

st.dataframe(df)

