import pandas as pd
import plotly.express as px
import requests
from scipy.stats import pearsonr  # For calculating correlation and p-value

# State abbreviations mapping
state_abbreviations = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

# Step 1: Download and prepare the CDC obesity data
url_obesity = "https://www.cdc.gov/obesity/media/files/2024/09/2023-Obesity-by-state.csv"
response_obesity = requests.get(url_obesity)
response_obesity.raise_for_status()  # Ensure request was successful
with open("2023-Obesity-by-state.csv", "wb") as file:
    file.write(response_obesity.content)

cdc_data = pd.read_csv("2023-Obesity-by-state.csv")
cdc_data.columns = cdc_data.columns.str.strip()
cdc_data = cdc_data.rename(columns={"State": "state", "Prevalence": "obesity_rate"})
cdc_data["state"] = cdc_data["state"].map(state_abbreviations)
cdc_data["obesity_rate"] = pd.to_numeric(cdc_data["obesity_rate"], errors="coerce")

# Step 2: Download and prepare the state integrity data
url_integrity = "https://cloudfront-files-1.publicintegrity.org/apps/2015/10/stateintegrity/0.1.35/data/overview.json"
response_integrity = requests.get(url_integrity)
response_integrity.raise_for_status()
data = response_integrity.json()

state_data = []
for state in data['states']:
    state_name = state['name']
    state_abbr = state_abbreviations.get(state_name, None)
    integrity_score = state['score']
    if state_abbr:
        state_data.append({"state": state_abbr, "integrity_score": integrity_score})

integrity_df = pd.DataFrame(state_data)
integrity_df["integrity_score"] = pd.to_numeric(integrity_df["integrity_score"], errors="coerce")

# Step 3: Merge the datasets
merged_data = pd.merge(cdc_data, integrity_df, on="state", how="inner").dropna(subset=["obesity_rate", "integrity_score"])

# Step 4: Calculate overall correlation
correlation, p_value = pearsonr(merged_data["obesity_rate"], merged_data["integrity_score"])
print(f"Correlation between obesity rate and integrity score: {correlation:.2f}")
print(f"P-value of the correlation: {p_value:.4f}")

if p_value < 0.05:
    print("The correlation is statistically significant at the 95% confidence level.")
else:
    print("The correlation is not statistically significant at the 95% confidence level.")

# Step 5: Create the first plot (obesity rate by state)
fig1 = px.choropleth(
    cdc_data,
    locations="state",
    locationmode="USA-states",
    color="obesity_rate",
    color_continuous_scale=["blue", "lightblue", "yellow", "orange", "red"],
    scope="usa",
    title="Adult Obesity Prevalence by State (2023) - Source CDC.org"
)
fig1.write_image("obesity_prevalence_map_2023.png", width=1024, height=768)

# Step 6: Create the second plot (integrity score by state)
fig2 = px.choropleth(
    integrity_df,
    locations='state',
    locationmode='USA-states',
    color='integrity_score',
    color_continuous_scale='Blues_r',
    scope='usa',
    title='State Integrity Scores by State (Darker = Lower Integrity) - Source publicintegrity.org'
)
fig2.write_image("state_integrity_map.png", width=1024, height=768)

# Step 7: Calculate a normalized composite metric for visualization
merged_data["combined_metric"] = (merged_data["obesity_rate"] + (100 - merged_data["integrity_score"])) / 200  # Normalize between 0 and 1

# Step 8: Create the third plot showing the normalized composite metric
fig3 = px.choropleth(
    merged_data,
    locations="state",
    locationmode="USA-states",
    color="combined_metric",
    color_continuous_scale="Purples",
    range_color=(0, 1),  # Ensures color scale goes from 0 to 1
    scope="usa",
    title="Normalized Composite Metric of Obesity Rate and Integrity Score (0 to 1 Scale)"
)
fig3.write_image("normalized_composite_metric_map.png", width=1024, height=768)

print("All plots have been saved as PNG files.")

