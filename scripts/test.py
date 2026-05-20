import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pandas as pd
import squarify

MIN_COUNTRIES = 20
MAX_COUNTRIES = 40

WRAP_LENGTH = 11

plt.rcParams.update(
    {
        "figure.figsize": (10, 6),
        "text.color": "#e6e6e6",
        "figure.facecolor": "#00000000",
        "axes.facecolor": "#00000000",
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#e6e6e6",
        "axes.labelsize": "large",
        "axes.titlesize": "x-large",
        "xtick.color": "#e6e6e6",
        "xtick.labelsize": "medium",
        "ytick.color": "#e6e6e6",
        "ytick.labelsize": "medium",
        "font.family": "sans-serif",
        "font.size": 12,
        "grid.color": "#000000",
        "grid.linestyle": "--",
        "legend.frameon": True,
        "legend.framealpha": 0.7,
        "path.simplify": True,
    }
)

COLORS = [
    "#cc241d",
    "#98971a",
    "#d79921",
    "#458588",
    "#b16286",
    "#689d6a",
    "#d65d0e",
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#fabd2f",
    "#b8bb26",
    "#fe8019",
    "#fb4934",
]


EURO_AREA = [
    "Austria",
    "Belgium",
    "Cyprus",
    "Estonia",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Ireland",
    "Italy",
    "Latvia",
    "Lithuania",
    "Luxembourg",
    "Malta",
    "Netherlands",
    "Portugal",
    "Slovakia",
    "Slovenia",
    "Spain",
]

EXCLUDE_LIST = [
    "Euro area",
    "Arab World",
    "East Asia & Pacific",
    "European Union",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
]


# Fetch the most recent current account balance data from the World Bank API
def fetch_current_account_data():
    return "data/current_account_data.csv"


def load_data(file_path):
    data = pd.read_csv(file_path)
    return data


# Process data to get the latest year available
def process_data(data, num_countries):
    latest_year = data.columns[
        -3
    ]  # Assuming the second last column is the most recent complete data year
    # Use first row as header
    data = data[["Country Name", latest_year]]
    data.columns = ["Country", "Current Account Balance"]
    data = data.dropna()
    data["Current Account Balance"] = pd.to_numeric(
        data["Current Account Balance"], errors="coerce"
    )
    data = data.dropna()

    data = data[~data["Country"].str.contains("|".join(EXCLUDE_LIST))]

    # Include top 30 countries/groups and aggregate the rest
    data["Absolute Value"] = data["Current Account Balance"].abs()
    data = data.sort_values("Absolute Value", ascending=False)
    top_n = data.head(num_countries)
    remaining = data.iloc[num_countries:]
    if not remaining.empty:
        aggregated_value = remaining["Current Account Balance"].sum()
        aggregated_row = pd.DataFrame(
            [{"Country": "Other", "Current Account Balance": aggregated_value}]
        )
        top_n = pd.concat([top_n, aggregated_row], ignore_index=True)

    return top_n


# Visualize using a treemap
def visualize_data(data):
    # Separate surplus and deficit
    surplus = data[data["Current Account Balance"] > 0]
    deficit = data[data["Current Account Balance"] < 0]

    # Wrap labels
    surplus["Country"] = surplus["Country"].str.wrap(WRAP_LENGTH)
    deficit["Country"] = deficit["Country"].str.wrap(WRAP_LENGTH)

    # Add value in billions to labels
    surplus["Country"] = (
        surplus["Country"]
        + "\n"
        + (surplus["Current Account Balance"] / 1e9).astype(int).astype(str)
    )
    deficit["Country"] = (
        deficit["Country"]
        + "\n"
        + (deficit["Current Account Balance"] / 1e9).astype(int).astype(str)
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.06, wspace=0.1)

    # Surplus
    squarify.plot(
        sizes=surplus["Current Account Balance"],
        label=surplus["Country"],
        alpha=0.8,
        ax=ax1,
        pad=True,
        color=COLORS[1],
    )
    ax1.axis("off")

    # Deficit
    squarify.plot(
        sizes=-deficit["Current Account Balance"],
        label=deficit["Country"],
        alpha=0.7,
        ax=ax2,
        pad=True,
        color=COLORS[0],
    )
    ax2.axis("off")

    fig.text(0.99, 0.04, 'Current Account Balance in 2022 (billion USD). Data source: World Bank', ha='right', fontsize=12)

    return fig


# Fetch, process and visualize the data
file_path = fetch_current_account_data()
data = load_data(file_path)

# Initialize variables to keep track of the best number of countries and the corresponding size of "Other"
best_num_countries = None
min_other_size = float("inf")

# Loop over the range of values for NUM_COUNTRIES
for num_countries in range(MIN_COUNTRIES, MAX_COUNTRIES):
    # Process the data
    processed_data = process_data(data, num_countries)

    # Check if "Other" is in the data
    if "Other" in processed_data["Country"].values:
        # Get the size of "Other"
        other_size = (
            processed_data.loc[
                processed_data["Country"] == "Other", "Current Account Balance"
            ]
            .abs()
            .values[0]
        )

        # If this is the smallest size of "Other" we've seen so far, update our best values
        if other_size < min_other_size:
            best_num_countries = num_countries
            min_other_size = other_size
print(f"Best number of countries: {best_num_countries}")

processed_data = process_data(data, best_num_countries)
fig = visualize_data(processed_data)

# Save the figure
fig.savefig("images/global_ca_balances.svg")
