from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

# Load your data
combined_df = pd.read_csv("outputs/combined_cleaned.csv")
combined_df["date"] = pd.to_datetime(combined_df["date"])

app = Dash(__name__)

app.layout = html.Div([
    html.H4('Price Change of Product Over Time'),

    # DROPDOWN menu for products
    dcc.Dropdown(
        id="product-dropdown",
        options=[
            {"label": model, "value": model}
            for model in sorted(combined_df["model"].unique())
        ],
        value=combined_df["model"].unique()[0],  # default selection
        multi=False  # set to True if you want multiple products
    ),
    dcc.RadioItems(
        id="mode-toggle",
        options=[
            {"label": "Actual", "value": "actual"},
            {"label": "Actual + Forecast", "value": "forecast"},
        ],
        value="actual",
        inline=True
        ),

    dcc.Graph(id="graph"),
])

@app.callback(
    Output("graph", "figure"),
    Input("product-dropdown", "value"),
    Input("mode-toggle", "value")
)
def update_line_chart(selected_model, mode):

    # Filter by selected product
    df = combined_df[combined_df["model"] == selected_model]

    # Same structure as before
    df = (
        df.groupby(["date", "site"])["price"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        df,
        x="date",
        y="price",
        color="site",  # each site = its own line
        title=f"{selected_model} Price Trends by Site"
    )

    # linear regression forecast :)
    if mode == "forecast":

        for site, site_df in df.groupby("site"):

            site_df = site_df.sort_values("date")

            site_df["date_num"] = site_df["date"].map(pd.Timestamp.toordinal)

            X = site_df["date_num"].values.reshape(-1, 1)
            y = site_df["price"].values

            if len(site_df) < 2:
                continue

            model = LinearRegression()
            model.fit(X, y)

            future_dates = pd.date_range(site_df["date"].max(), periods=30)
            future_X = future_dates.map(pd.Timestamp.toordinal).values.reshape(-1, 1)

            preds = model.predict(future_X)

            fig.add_scatter(
                x=future_dates,
                y=preds,
                mode="lines",
                line=dict(dash="dash"),
                name=f"{site} forecast"
            )
    return fig

app.run(host="0.0.0.0", port=5000, debug=False)
