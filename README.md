# Scouting Platform
https://www.youtube.com/watch?v=_2MwqZBeyk0

This project is an Interactive Scouting Platform designed to centralize and automate the collection, processing, and analysis of football player data. It provides a customizable, low-cost alternative to commercial scouting tools, allowing users to align statistical analysis with their specific club philosophy.

## Overview

The platform integrates performance metrics with market data to provide a 360-degree view of players. It allows scouts and analysts to generate personalized rankings, compare athletes, and identify strategic market opportunities.

## Data Sources

The application utilizes data from open-access sources to ensure comprehensive coverage:

- **FBRef**: For advanced performance metrics such as Expected Goals (xG), Expected Assists (xAG), progressive passes, and defensive actions.  
- **Transfermarkt**: For market values, contractual status, and player biographical data (age, height, preferred foot) for male players.  
- **Soccerdonna**: For market values and biographical data specifically for women's football.

## Key Features

- **Custom Performance Indices**: Create your own evaluation models by selecting specific metrics and assigning weights that total 1.0.  
- **Advanced Filtering**: Filter players by age, position, league, preferred foot, height, and market value.  
- **Player Comparisons**: Generate interactive radar charts to compare the profiles of multiple players side-by-side.  
- **Automated Notifications**: Set up email alerts when new players matching your scouting criteria are identified.  
- **Data Export**: Export filtered player lists and rankings directly to CSV for daily scouting workflow integration.

## Tech Stack

- **Language**: Python  
- **Data Processing**: Pandas, NumPy  
- **Visualization**: Plotly, mplsoccer  
- **Web Interface**: Streamlit  

## Methodology

The project follows the **CRISP-DM (Cross Industry Standard Process for Data Mining)** framework:

- **Data Preparation**: Cleaning, removing duplicates, and normalizing metrics.  
- **Metric Standardization**: All absolute values are converted to per-90-minute indicators to ensure fair comparison between players with different playing times.  
- **Normalization**: Min-max normalization is applied to allow different metrics to be compared on the same scale.


<img width="546" height="309" alt="Captura de ecrã 2026-02-13, às 17 00 38" src="https://github.com/user-attachments/assets/9052fc6d-b883-49e3-bcbb-fae3c03a420c" />
<img width="541" height="306" alt="Captura de ecrã 2026-02-13, às 17 00 49" src="https://github.com/user-attachments/assets/311fe763-f4ed-4611-897e-955bd18f3361" />
<img width="508" height="268" alt="Captura de ecrã 2026-02-13, às 17 01 01" src="https://github.com/user-attachments/assets/71d0c7b3-d91c-46da-ba08-439253ac3afe" />
<img width="513" height="266" alt="Captura de ecrã 2026-02-13, às 17 01 11" src="https://github.com/user-attachments/assets/c166571c-1591-4280-9af8-b21d0281c2e7" />
<img width="512" height="268" alt="Captura de ecrã 2026-02-13, às 17 01 24" src="https://github.com/user-attachments/assets/0eb3a690-1e53-4426-af9c-4b6533b6f17e" />
<img width="512" height="271" alt="Captura de ecrã 2026-02-13, às 17 01 36" src="https://github.com/user-attachments/assets/79e44b8c-f908-4d8d-b4c6-1d21256860da" />
<img width="545" height="307" alt="Captura de ecrã 2026-02-13, às 17 01 52" src="https://github.com/user-attachments/assets/fc07ffc7-da0c-4b79-b713-7a21258395e8" />
<img width="500" height="338" alt="Captura de ecrã 2026-02-13, às 17 02 04" src="https://github.com/user-attachments/assets/93b0771c-e60a-4c9e-a339-c407b70b8ba0" />
