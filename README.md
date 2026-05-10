# gisci343-a2-pt
Assignment 2
# IKEA Sylvia Park Public Transport Dashboard

An interactive urban analytics dashboard exploring public transport patronage for bus routes serving IKEA Sylvia Park in Auckland, New Zealand.

The dashboard was developed using **Shiny for Python** and deployed using **shinylive on GitHub Pages**.

## Dashboard purpose

This application investigates whether bus patronage changed following the opening of IKEA Sylvia Park. Users can explore:
- Bus patronage trends over time
- Changes before and after the IKEA opening
- Bus routes and nearby stops serving the Sylvia Park area
- Percentage change in average patronage by route

The dashboard is designed for transport planning and urban analytics purposes.

---

## Features

- Interactive route, area, and period filters
- Interactive map of nearby (within 1km) bus routes and stops
- Time-series patronage analysis using Plotly
- Comparative summary table with percentage changes
- Dynamic reactive filtering
- Browser-based deployment using shinylive

---

## Technologies used

- Python
- Shiny for Python
- shinylive
- pandas
- GeoPandas
- Plotly
- ipyleaflet

---

## Project structure

```text
basic-app/
    app.py
    data/

docs/
screenshots/
design_report.qmd
README.md