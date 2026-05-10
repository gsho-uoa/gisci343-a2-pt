from shiny import App, render, ui, reactive
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, GeoData
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd
import plotly.express as px
from ipyleaflet import Marker, AwesomeIcon
from ipywidgets import HTML

# Load cleaned data
patronage = pd.read_csv("data/patronage_ikea.csv")
routes = gpd.read_file("data/routes_1km.gpkg").to_crs(4326)
stops = gpd.read_file("data/stops_1km.gpkg").to_crs(4326)
closest_stop = pd.read_csv("data/closest_stop_summary.csv")

# IKEA point and buffer for map
ikea = gpd.GeoDataFrame(
    {"name": ["IKEA Sylvia Park"]},
    geometry=[Point(174.84644611668557, -36.916075676043036)],
    crs="EPSG:4326",
)

ikea_buffer = ikea.to_crs(2193).buffer(1000)
ikea_buffer = gpd.GeoDataFrame(
    {"name": ["1 km buffer"]},
    geometry=ikea_buffer,
    crs="EPSG:2193",
).to_crs(4326)

route_choices = ["All"] + sorted(patronage["Route No"].astype(str).unique())
area_choices = ["All"] + sorted(patronage["Area"].dropna().unique())

app_ui = ui.page_fluid(

    ui.h3("IKEA Sylvia Park Public Transport Dashboard"),

    ui.p(
        "This dashboard explores public transport patronage for bus routes serving IKEA Sylvia Park. "
        "Use the filters to compare route demand before and after the IKEA opening."
    ),

    # Top filter bar
    ui.layout_columns(
    ui.card(
        ui.card_header("Route"),
        ui.input_radio_buttons(
            "route",
            None,
            choices=["All", "298", "32", "323", "66", "74", "782"],
            selected="All",
            inline=True
        ),
        style="min-height: 90px;"
    ),

    ui.card(
        ui.card_header("Area"),
        ui.input_select("area", None, choices=area_choices, selected="All"),
        style="min-height: 90px;"
    ),

    ui.card(
        ui.card_header("Period"),
        ui.input_select("period", None, choices=["All", "Before IKEA", "After IKEA"], selected="All"),
        style="min-height: 90px;"
    ),

    ui.card(
        ui.card_header("Reset"),
        ui.input_action_button("reset", "Reset filters", width="100%"),
        style="min-height: 90px;"
    ),

    col_widths=(5, 3, 3, 1)
),

    ui.output_text("summary"),

    # Main dashboard row
    ui.layout_columns(

        ui.card(
            ui.card_header("Patronage over time"),
            output_widget("chart")
        ),

        ui.card(
            ui.card_header("Bus routes and stops near IKEA"),
            output_widget("map")
        ),

        ui.card(
            ui.card_header("Average patronage by route"),
            ui.output_table("route_summary")
        ),

        col_widths=(4, 5, 3)
    ),

    title="IKEA Sylvia Park Transport Dashboard"
)


def server(input, output, session):
    @reactive.effect
    @reactive.event(input.reset)
    def _():
        all_routes = sorted(patronage["Route No"].astype(str).unique().tolist())
        ui.update_radio_buttons(
            "route",
            selected="All"
        )

        ui.update_select(
            "area",
            selected="All"
        )

        ui.update_select(
            "period",
            selected="All"
        )
    @reactive.calc
    def filtered_patronage():
        df = patronage.copy()

        selected_routes = input.route()

        if selected_routes != "All":
            df = df[df["Route No"].astype(str) == selected_routes]
        
        if input.area() != "All":
            df = df[df["Area"] == input.area()]

        if input.period() != "All":
            df = df[df["Period"] == input.period()]

        return df

    @render.text
    def summary():
        df = filtered_patronage()
        avg = df["Boardings"].mean()

        stop_name = closest_stop["stop_name"].iloc[0]
        distance = closest_stop["distance_m"].iloc[0]

        return (
            f"Showing {df['Route No'].nunique()} route(s) and {len(df)} monthly records. "
            f"Average boardings per service hour: {avg:.2f}. "
            f"Closest stop to IKEA: {stop_name} ({distance} m)."
        )

    @render_widget
    def map():
        m = Map(center=(-36.91782, 174.84472), zoom=14)

        selected_routes=input.route()
        if selected_routes == "All":
            map_routes= routes.copy()
        else:
            map_routes = routes[routes["ROUTENUMBER"].astype(str) == selected_routes].copy()

        ikea_marker = Marker(
            location=(-36.91782, 174.84472),
            draggable=False,
            icon=AwesomeIcon(
                name="shopping-cart",
                marker_color="red",
                icon_color="white"
            )
        )

        ikea_marker.popup = HTML("<b>IKEA</b>")
        m.add_layer(ikea_marker)

        route_colours = {
        "298": "#636EFA",
        "32": "#EF553B",
        "323": "#00CC96",
        "66": "#AB63FA",
        "74": "#FFA15A",
        "782": "#19D3F3"
        }

        for route_no, colour in route_colours.items():

            route_layer = map_routes[
                map_routes["ROUTENUMBER"].astype(str) == route_no
            ]

            if not route_layer.empty:
                m.add_layer(
                    GeoData(
                        geo_dataframe=route_layer,
                        name=f"Route {route_no}",
                        style={
                         "color": colour,
                            "weight": 4,
                            "opacity": 0.8,
                         }
                    )
                )

        for _, stop in stops.iterrows():

            stop_marker = Marker(
                location=(stop.geometry.y, stop.geometry.x),
                draggable=False,
                icon=AwesomeIcon(
                    name="bus",
                    marker_color="blue",
                    icon_color="white",
                    icon_size=[20,20]
                )
            )
            stop_marker.popup = HTML(
                f"<b>{stop['STOPNAME']}</b>"
            )
            m.add_layer(stop_marker)

        return m  


    @render_widget
    def chart():
        df = filtered_patronage().copy()
        df["Month"] = pd.to_datetime(df["Month"], format="%b %Y")
        df = df.sort_values("Month")
        
        if df.empty:
            fig = px.line(title="No patronage data for selected filters")
            return fig

        df["Month"] = pd.to_datetime(df["Month"], format="%b %Y")
        df=df.sort_values("Month")
    

        route_colours = {
            "298": "#636EFA",
            "32": "#EF553B",
            "323": "#00CC96",
            "66": "#AB63FA",
            "74": "#FFA15A",
            "782": "#19D3F3"
        }

        df["Route No"] = df["Route No"].astype(str)

        fig = px.line(
            df,
            x="Month",
            y="Boardings",
            color="Route No",
            markers=True,
            title="Patronage trends for routes serving IKEA Sylvia Park",
            color_discrete_map=route_colours
        )

        fig.add_vline(
            x=pd.to_datetime("2025-12-01"),
            line_dash="dash",
        )

        fig.add_annotation(
            x=pd.to_datetime("2025-12-01"),
            y=df["Boardings"].max(),
            text="IKEA opens",
            showarrow=True,
            arrowhead=2,
            yshift=10
        )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Boardings per service hour",
            legend_title="Route",
        )

        return fig

    @render.table
    def route_summary():

        df = patronage.copy()

        if input.route() != "All":
            df = df[df["Route No"].astype(str) == input.route()]
        
        if input.area() != "All":
            df = df[df["Area"] == input.area()]

        if df.empty:
            return pd.DataFrame({
                "Message":["No data for selected filters"]
            })

        summary = (
            df.groupby(["Route No","Period"])["Boardings"]
            .mean()
            .reset_index()
            .round(2)
        )

        pivot = summary.pivot(
            index="Route No",
            columns="Period",
            values="Boardings"
        )
        pivot["Change"] = (
            pivot["After IKEA"] - pivot["Before IKEA"]
        ).round(2)
        pivot.columns.name = None
        return pivot.reset_index()

app = App(app_ui, server)