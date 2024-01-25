import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
from pandas.tseries.offsets import QuarterEnd
register_matplotlib_converters()

plt.rcParams.update({
    'figure.figsize': (10, 6),
    'text.color': '#e6e6e6',
    'figure.facecolor': '#00000000',
    'axes.facecolor': '#00000000',
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#e6e6e6',
    'axes.labelsize': 'large',
    'axes.titlesize': 'x-large',
    'xtick.color': '#e6e6e6',
    'xtick.labelsize': 'medium',
    'ytick.color': '#e6e6e6',
    'ytick.labelsize': 'medium',
    'font.family': 'sans-serif',
    'grid.color': '#000000',
    'grid.linestyle': '--',
    'legend.frameon': True,
    'legend.framealpha': 0.7,
    'path.simplify': True
})


def parse_date(string, freq):
    """
    Converts a string in the format 'YYYY-QX' to a datetime object representing the end of the quarter.
    """
    if freq == "Q":
        year, quarter = string.split('-Q')
        return pd.to_datetime(year) + QuarterEnd(int(quarter))
    return pd.to_datetime(string)


def get_imf_data(indicators, country_codes, start_date, end_date, freq="A", db="IFS"):
    indicators = '+'.join(indicators)
    country_codes = '+'.join(country_codes)
    url = f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/{db}/{freq}.{country_codes}.{indicators}?startPeriod={start_date}&endPeriod={end_date}"
    print(url)
    response = requests.get(url)
    result = response.json()['CompactData']['DataSet']['Series']
    dfs = []
    if not isinstance(result, list):
        result = [result]
    for series in result:
        obs_values = [obs["@OBS_VALUE"] for obs in series["Obs"]]
        obs_dates = [obs["@TIME_PERIOD"] for obs in series["Obs"]]
        temp_df = pd.DataFrame(obs_values, index=obs_dates)
        temp_df.index = temp_df.index.map(lambda x: parse_date(x, freq))
        # Rename the column using the '@INDICATOR' value
        indicator = series['@INDICATOR']
        temp_df.columns = [indicator]
        # Convert values to numeric, coerce errors
        temp_df[indicator] = pd.to_numeric(temp_df[indicator], errors='coerce')
        dfs.append(temp_df)

    result = pd.concat(dfs, axis=1)
    return result


def get_wdi_data(indicators, country_codes, start_year=1980, end_year=2023):
    indicators_url = ';'.join(indicators)
    country_codes = ';'.join(country_codes)
    url = f"http://api.worldbank.org/v2/country/{country_codes}/indicator/{indicators_url}?source=2"
    print(url)
    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 500  # Ensuring we get all data in one request
    }
    response = requests.get(url, params=params)
    data = response.json()[1]  # The actual data is in the second item of the response
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    print(df.head())
    df_pivot = df.pivot(index='date', columns='countryiso3code', values=indicators)
    return df_pivot



def create_plot(data, xlabel, ylabel, data_source=None, secondary_y=None, secondary_y_label=None, plot_type="line", bar_width=50, ymin=None, legend=False):
    print(f"Plot type: {plot_type}")
    primary_colors = [
        '#cc241d',
        '#98971a',
        '#d79921',
        '#458588',
        '#b16286',
        '#689d6a',
        '#d65d0e',
    ]
    secondary_colors = [
        '#83a598',
        '#d3869b',
        '#8ec07c',
        '#fabd2f',
        '#b8bb26',
        '#fe8019',
        '#fb4934',
    ]
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    n_datasets = len(data.columns)
    bar_width_total = bar_width * n_datasets

    # Plot data on the primary y-axis
    primary_cols = data.columns.difference(secondary_y) if secondary_y else data.columns
    for i, col in enumerate(primary_cols):
        color = primary_colors[i % len(primary_colors)]
        if plot_type == 'line':
            print("Line!!!")
            ax.plot(data.index, data[col], label=col, color=color)
        elif plot_type == 'bar':
            print("Bar!!!")
            # Calculate offset for each bar
            offset = (i - n_datasets / 2) * bar_width + bar_width / 2
            # Shift position of each bar
            bar_positions = np.arange(len(data)) + offset
            ax.bar(bar_positions, data[col], label=col, color=color, width=bar_width)

    # Enhance the plot with titles and labels
    ax.set_xlabel(xlabel, fontsize=12, color='lightgrey')
    ax.set_ylabel(ylabel, fontsize=12, color='lightgrey')
    ax.set_ylim(bottom=ymin)

    # Improve the grid, ticks, and layout
    ax.grid(True, which='both', color='gray', linestyle='--', linewidth=0.5)
    ax.tick_params(colors='white', which='both')  # Tick colors

    # Plot data on the secondary y-axis, if specified
    if secondary_y:
        ax2 = ax.twinx()
        for i, col in enumerate(secondary_y):
            color = secondary_colors[i % len(secondary_colors)]
            if plot_type == 'line':
                ax2.plot(data.index, data[col], label=col, color=color)
            elif plot_type == 'bar':
                # Calculate offset for each bar
                offset = (i - n_datasets / 2) * bar_width + bar_width / 2
                # Shift position of each bar
                bar_positions = np.arange(len(data)) + offset
                print(f"bar positions: {bar_positions}")
                ax2.bar(bar_positions, data[col], label=col, color=color, alpha=0.7, width=bar_width)
        ax2.set_ylim(bottom=ymin)

        # Set secondary y-axis label if needed
        ax2.set_ylabel(secondary_y_label or secondary_y[0], fontsize=12, color='lightgrey')

    # Add a legend
    lines, labels = ax.get_legend_handles_labels()
    if secondary_y:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines += lines2
        labels += labels2
    if legend or secondary_y:
        ax.legend(lines, labels)

    if data_source:
        ax.text(1, -0.15, "Quelle: " + data_source, transform=ax.transAxes, fontsize=8, va='bottom', ha='right', color='darkgrey')

    plt.tight_layout()

    return fig


def create_bar_plot(data, xlabel, ylabel, data_source=None, secondary_y=None, secondary_y_label=None, plot_type='line', bar_width=0.15):
    primary_colors = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow', 'black']
    secondary_colors = ['orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'lime']
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Convert index to string if it's a datetime
    if isinstance(data.index, pd.DatetimeIndex):
        data.index = data.index.strftime('%Y-%m-%d')

    # Plot data
    if plot_type == 'line':
        for i, col in enumerate(data.columns):
            ax.plot(data.index, data[col], label=col, color=primary_colors[i % len(primary_colors)])
    elif plot_type == 'bar':
        data.plot(kind='bar', ax=ax, color=primary_colors[:len(data.columns)], width=bar_width)

    # Rest of your code for enhancing the plot, adding secondary y-axis, etc.

    return fig


def india_catch_up(file_path):
    # Indicators
    gdp_per_capita = "NY.GDP.PCAP.CD"  # GDP per capita (current US$)
    # Fetch data for India and USA
    df = get_wdi_data([gdp_per_capita], ["IN", "US"])
    # Calculate the india_catch_up ratio
    df['india_catch_up'] = 100 * df['IND'] / df['USA']
    data = df[['india_catch_up']]
    fig = create_plot(data, "Jahr", "% des pro Kopf Einkommen in USA", "World Bank national accounts data")
    fig.savefig(file_path, format='svg')


def india_tech(file_path):
    df = get_wdi_data(["TX.MNF.TECH.ZS.UN"], ["IN"])
    # Calculate the india_catch_up ratio
    fig = create_plot(df, "Jahr", "% der Industrieexporte", "United Nations Industrial Development Organization (UNIDO), Competitive Industrial Performance (CIP) database")
    fig.savefig(file_path, format='svg')


def csv_plot(csv_path, output_path, xlabel, ylabel, source, y2=None, y2label=None):
    df = pd.read_csv(csv_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    fig = create_plot(df, xlabel, ylabel, source, y2, y2label)
    fig.savefig(output_path, format='svg')


def thailand_ca_balance(file_path):
    indicators = {
        "BCAXF_BP6_USD": "Leistungsbilanzsaldo (links)",
    }
    df = get_imf_data(indicators.keys(), ["TH"], 1990, 2002, freq="Q")
    df.rename(columns=indicators, inplace=True)
    fig = create_plot(
        df,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF): International Financial Statistics",
    )
    fig.savefig(file_path, format='svg')


def thailand_ext_debt(file_path):
    indicators = {
        "ILD_BP6_USD": "liab_direct_investment",
        "ILP_BP6_USD": "liab_portfolio",
        "ENDA_XDC_USD_RATE": "thb_usd",
    }
    df = get_imf_data(indicators.keys(), ["TH"], 1990, 1999, freq="A")
    df.rename(columns=indicators, inplace=True)
    df['Auslandsverschuldung in USD (links)'] = df['liab_direct_investment'] + df['liab_portfolio']
    df['Auslandsverschuldung in THB (rechts)'] = df['Auslandsverschuldung in USD (links)'] * df["thb_usd"]

    df = df[['Auslandsverschuldung in USD (links)', 'Auslandsverschuldung in THB (rechts)']]

    fig = create_plot(
        df,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF): International Financial Statistics",
        secondary_y=["Auslandsverschuldung in THB (rechts)"],
        secondary_y_label="Mio. THB",
        ymin=0
    )
    fig.savefig(file_path, format='svg')

    
def thailand_forex(file_path):
    indicators = {
        "RAXGFX_USD": "Währungsreserven der Zentralbank",
        "ENDA_XDC_USD_RATE": "THB/USD (rechts)",
    }
    df = get_imf_data(indicators.keys(), ["TH"], 1990, 2002, freq="Q")
    df.rename(columns=indicators, inplace=True)
    fig = create_plot(
        df,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF): International Financial Statistics",
        secondary_y=[indicators["ENDA_XDC_USD_RATE"]],
        secondary_y_label="THB/USD"
    )
    fig.savefig(file_path, format='svg')


def thailand_gdp_per_capita(file_path):
    df = get_wdi_data(["NY.GDP.PCAP.CD"], ["TH"], start_year=1990, end_year=2002)
    # Calculate the india_catch_up ratio
    fig = create_plot(df, "Jahr", "USD", "World Bank national accounts data, and OECD National Accounts data files.")
    fig.savefig(file_path, format='svg')

    
def world_co2(file_path):
    indicators = {
        "EN.ATM.CO2E.PC": "CO2-Emissionen (links)",
        "EN.ATM.CO2E.PP.GD": "CO2-Effizienz (rechts)",
    }
    df = get_wdi_data(indicators.keys(), ["1W"], 1990, 2022)
    df.rename(columns=indicators, inplace=True)
    fig = create_plot(
        df,
        "Jahr",
        "t pro Kopf",
        "Climate Watch",
        secondary_y=[indicators["EN.ATM.CO2E.PP.GD"]],
        secondary_y_label="kg pro USD BIP in KKP"
    )
    fig.savefig(file_path, format='svg')


def raw_materials(file_path):
    df = pd.read_csv("data/raw_materials.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    print(df.head())
    first_row = df.iloc[0]
    df['Kupfer'] = df['copper'] / first_row['copper'] * 100
    df['Steinkohle'] = df['coal'] / first_row['coal'] * 100
    df['Erdöl'] = df['oil'] / first_row['oil'] * 100
    df = df[['Kupfer', 'Steinkohle', 'Erdöl']]
    fig = create_plot(df, "Jahr", "Index (1990: 100)", "Federal Reserve Bank of Saint Louis", legend=True)
    fig.savefig(file_path, format='svg')


if __name__ == '__main__':
    data_path = "data/"
    image_path = "images/"
    # india_catch_up(image_path + 'india_catch_up.svg')
    # csv_plot(data_path + 'india_fdi_gdp.csv', image_path + 'india_fdi_gdp.svg', "Jahr", "% des BIP", "United Nations Conference on Trade and Development (UNCTAD) statistical data")
    # india_tech(image_path + 'india_tech_exports.svg')
    # thailand_ca_balance(image_path + 'thailand_ca_balance.svg')
    # thailand_forex(image_path + 'thailand_forex.svg')
    # thailand_ext_debt(image_path + 'thailand_ext_debt.svg')
    # thailand_gdp_per_capita(image_path + 'thailand_gdp_per_capita.svg')
    # csv_plot(
    #     data_path + 'world_co2.csv',
    #     image_path + 'world_co2.svg',
    #     "Jahr",
    #     "kt",
    #     "Climate Watch"
    # )
    raw_materials(image_path + 'raw_materials.svg')
    plt.show()
    


