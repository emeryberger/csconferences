import pandas as pd
import matplotlib.pyplot as plt

# Read in the data from the CSV file
conf_data = pd.read_csv("conferences.csv")

# Get a list of conference names from the CSV file
conference_list = conf_data['Conference'].unique().tolist()

# Parse command line arguments
import argparse
parser = argparse.ArgumentParser(description="Publication analysis for conferences")
parser.add_argument("conference_name", help="Name of conference to analyze", choices=conference_list)

args = parser.parse_args()

if not args.conference_name:
    print_help()
else:
    # Filter the data by conference
    conference_data = conf_data[conf_data["Conference"] == args.conference_name]

# Filter the data by conference
conference_name = args.conference_name
conf_data = conf_data.loc[conf_data["Conference"] == conference_name]

print(conf_data)

# Create a bar plot of acceptance rates by year
#plt.bar(conf_data["Year"], conf_data["Papers accepted"] / conf_data["Papers submitted"])

# Calculate the number of accepted and rejected papers for each year
conf_data["Rejected"] = conf_data["Submitted"] - conf_data["Accepted"]

# Create a stacked bar plot of accepted and rejected papers by year
plt.bar(conf_data["Year"], conf_data["Accepted"], label="Accepted", color="green")
plt.bar(conf_data["Year"], conf_data["Rejected"], bottom=conf_data["Accepted"], label="Rejected", color="red")

# Set the x-axis label
plt.xlabel("Year")

# Set the y-axis label
plt.ylabel("Accepted / Rejected Papers")

# Set the title of the plot
plt.title(f"{conference_name} Conference Publications by Year")

# Show the plot
plt.show()
