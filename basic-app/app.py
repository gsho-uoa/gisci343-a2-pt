from shiny import App, ui, render, reactive
import pandas as pd
import matplotlib.pyplot as plt

# Inline sample data (replace with real data next week)
suburbs = pd.DataFrame({
    "suburb":        ["Ponsonby", "Parnell", "Mt Eden", "Newmarket",
                      "Grey Lynn", "Remuera", "Onehunga", "Henderson"],
    "population":    [12500, 8900, 15300, 11200, 14800, 9600, 13500, 21000],
    "median_income": [75000, 95000, 68000, 82000, 71000, 105000, 58000, 52000],
})

app_ui = ui.page_fluid(
    ui.h2("Auckland suburbs explorer"),
    ui.p("Filter suburbs by minimum population and see how incomes compare."),
    ui.input_slider("min_pop", "Minimum population", 0, 25000, 0, step=1000),
    ui.output_text("summary"),
    ui.output_table("tbl"),
    ui.output_plot("chart"),
)

def server(input, output, session):

    @reactive.calc
    def filtered():
        return suburbs[suburbs["population"] >= input.min_pop()]

    @render.text
    def summary():
        df = filtered()
        if len(df) == 0:
            return "No suburbs match the current filter."
        return f"{len(df)} suburbs, mean income ${df['median_income'].mean():,.0f}."

    @render.table
    def tbl():
        return filtered()

    @render.plot
    def chart():
        df = filtered()
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.barh(df["suburb"], df["median_income"], color="steelblue")
        ax.set_xlabel("Median income (NZ$)")
        ax.set_title("Median income by suburb")
        plt.tight_layout()
        return fig

app = App(app_ui, server)