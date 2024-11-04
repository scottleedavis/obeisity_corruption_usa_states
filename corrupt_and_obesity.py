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
try:
    response_obesity = requests.get(url_obesity)
    response_obesity.raise_for_status()  # Ensure request was successful
    with open("2023-Obesity-by-state.csv", "wb") as file:
        file.write(response_obesity.content)
except requests.exceptions.RequestException as e:
    print(f"Error downloading CDC obesity data: {e}")

# Load and clean the CDC obesity data
cdc_data = pd.read_csv("2023-Obesity-by-state.csv")
cdc_data.columns = cdc_data.columns.str.strip()  # Remove whitespace from column names
cdc_data = cdc_data.rename(columns={"State": "state", "Prevalence": "obesity_rate"})
cdc_data["state"] = cdc_data["state"].str.strip().map(state_abbreviations)
cdc_data["obesity_rate"] = pd.to_numeric(cdc_data["obesity_rate"], errors="coerce")

# Step 2: Create the first choropleth map for obesity rates
fig = px.choropleth(
    cdc_data,
    locations="state",
    locationmode="USA-states",
    color="obesity_rate",
    color_continuous_scale=["blue", "lightblue", "yellow", "orange", "red"],  # Explicit blue-to-red scale
    scope="usa",
    title="Adult Obesity Prevalence by State (2023) - Source CDC.org"
)
fig.show()

# Step 3: Download and prepare the state integrity data
url_integrity = "https://cloudfront-files-1.publicintegrity.org/apps/2015/10/stateintegrity/0.1.35/data/overview.json"
try:
    response_integrity = requests.get(url_integrity)
    response_integrity.raise_for_status()
    data = response_integrity.json()
except requests.exceptions.RequestException as e:
    print(f"Error downloading state integrity data: {e}")

# Process the integrity data
state_data = []
for state in data['states']:
    state_name = state['name']
    state_abbr = state_abbreviations.get(state_name, None)
    integrity_score = state['score']
    if state_abbr:
        state_data.append({"state": state_abbr, "integrity_score": integrity_score})

integrity_df = pd.DataFrame(state_data)
integrity_df["integrity_score"] = pd.to_numeric(integrity_df["integrity_score"], errors="coerce")

# Step 4: Create the second choropleth map with darker colors for lower integrity scores
fig = px.choropleth(
    integrity_df,
    locations='state',
    locationmode='USA-states',
    color='integrity_score',
    color_continuous_scale='Blues_r',  # Use the reversed 'Blues' scale for lack of integrity
    scope='usa',
    title='State Integrity Scores by State (Darker = Lower Integrity) - Source publicintegrity.org'
)
fig.show()

# Step 5: Merge the two datasets on state abbreviation
merged_data = pd.merge(cdc_data, integrity_df, on="state", how="inner").dropna(subset=["obesity_rate", "integrity_score"])

# Step 6: Calculate the correlation between obesity rate and integrity score with significance testing
if not merged_data.empty:
    correlation, p_value = pearsonr(merged_data["obesity_rate"], merged_data["integrity_score"])
    print(f"Correlation between obesity rate and integrity score: {correlation:.2f}")
    print(f"P-value of the correlation: {p_value:.4f}")

    # Step 7: Check if the correlation is statistically significant at the 95% confidence level
    if p_value < 0.05:
        print("The correlation is statistically significant at the 95% confidence level.")
    else:
        print("The correlation is not statistically significant at the 95% confidence level.")
else:
    print("Merged data is empty after cleaning. Cannot calculate correlation.")

# Step 8: Create the third choropleth map for integrity score and obesity rate correlation
fig = px.choropleth(
    merged_data,
    locations="state",
    locationmode="USA-states",
    color="integrity_score",
    hover_data={"obesity_rate": True, "integrity_score": True},
    color_continuous_scale="Reds",
    scope="usa",
    title=f"Correlation of Obesity Rate and Integrity Score by State\n"
          f"(Darker Red = Higher Corruption and Obesity Correlation)"
)
fig.show()
