
🌍 EARTHPULSE

NASA Earth System Trend Analyzer

Understanding Earth's changing climate through NASA data.

EARTHPULSE is a climate data analysis and visualization platform developed for the NASA Space Apps Challenge 2026. It helps users explore climate trends in Kerala, India, using NASA POWER data and statistical analysis.

Our goal is to make climate information easier to understand through interactive visualizations, meaningful insights, and accessible data analysis.

---

🚀 Project Overview

Climate change affects temperature, rainfall patterns, ecosystems, and communities. Understanding long-term climate trends is essential for making informed decisions.

EARTHPULSE provides an interactive platform where users can:

- Explore historical temperature trends.
- Analyze monthly and yearly rainfall patterns.
- Visualize climate data through interactive charts.
- Compare climate patterns across selected locations.
- Examine long-term trends using statistical methods.
- Understand changes in regional climate conditions.

🛰️ Data Source

Our project uses NASA POWER (Prediction Of Worldwide Energy Resources) data.

Climate parameters include:

Parameter| Description
T2M| Temperature at 2 metres above the surface
PRECTOTCORR| Corrected precipitation

The application retrieves historical monthly climate data through the NASA POWER API.

Data source: https://power.larc.nasa.gov/

📊 Statistical Analysis

EARTHPULSE uses statistical techniques to investigate climate trends, including:

- Theil-Sen Estimator: Estimates the magnitude of a trend.
- Mann-Kendall Test: Evaluates whether a monotonic trend is statistically significant.
- Kendall's Tau: Measures the strength and direction of a monotonic relationship.

Statistical results should be interpreted in the context of the selected location, time period, and available data.

✨ Key Features

- Interactive climate dashboard.
- Historical temperature and precipitation analysis.
- Location-based climate exploration.
- Interactive charts and visualizations.
- Statistical trend analysis.
- NASA POWER data integration.
- Accessible presentation of climate information.

🛠️ Technology Stack

Technology| Purpose
Python| Core programming language
Streamlit| Interactive web application
Pandas| Data processing
NumPy| Numerical computation
SciPy| Statistical analysis
Plotly| Interactive visualizations
NASA POWER API| Climate data source

🏗️ Project Structure

Earthpulse/
│
├── app.py
├── frontend/
│   └── components/
│       ├── sidebar.py
│       ├── cards.py
│       ├── charts.py
│       └── data_adapter.py
│
├── backend/
│   ├── __init__.py
│   ├── data_service.py
│   └── trend_analysis.py
│
├── requirements.txt
└── README.md

👥 Team Members & Contributions

EARTHPULSE was developed collaboratively by our team. Both members contributed to building, developing, integrating, and improving the project.

1. Devu

Role: Project Development & Integration

Contributions:

- Project development and implementation.
- Frontend development and dashboard integration.
- Project coordination and GitHub management.
- Testing, debugging, and overall integration.

2. Sharon Binu George

Role: Backend Development & Data Analysis

Contributions:

- Backend data service development.
- NASA POWER API integration.
- Climate data processing.
- Statistical trend analysis.
- Backend and frontend integration support.

Both team members collaborated throughout the development process. The responsibilities above describe their primary areas of contribution and do not imply that either member worked independently.

🖥️ Live Application

Live Demo: [Insert your deployed Streamlit application URL here]

GitHub Repository: https://github.com/krizzdev7/Earthpulse

▶️ Run Locally

Clone the repository:

git clone https://github.com/krizzdev7/Earthpulse.git

Navigate into the project:

cd Earthpulse

Install dependencies:

pip install -r requirements.txt

Run the application:

python -m streamlit run app.py

🌱 Impact & Future Scope

EARTHPULSE aims to make NASA climate data more accessible and understandable.

Future improvements may include:

- Expanding climate analysis to more regions.
- Adding additional environmental parameters.
- Improving regional climate comparisons.
- Adding more advanced visualization and analytical tools.
- Developing further educational climate insights.

🤖 Use of AI Tools

AI-assisted tools were used during development for programming assistance, debugging, documentation, and improving development workflows. The team reviewed and integrated the resulting work into the project.

🙏 Acknowledgements

- NASA POWER Project for providing accessible climate data.
- NASA Space Apps Challenge 2026.
- Everyone who supported and contributed to the development of EARTHPULSE.

---

Built collaboratively with curiosity, teamwork, and a shared passion for understanding our planet. 🌍

EARTHPULSE — Explore Earth's Climate. Understand Its Changes.