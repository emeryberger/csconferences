import pandas as pd
import matplotlib.pyplot as plt
import sys

filename = "conferences.csv"

# Read in the data from the CSV file
full_conf_data = pd.read_csv(filename)

# Get a list of conference names from the CSV file
conference_list = full_conf_data['Conference'].unique().tolist()

# Parse command line arguments
import argparse
parser = argparse.ArgumentParser(description="Publication analysis for conferences")
parser.add_argument("--conference_name", help="Name of conference to analyze", choices=conference_list)
parser.add_argument("--all", dest="all", action="store_const", const=True, help="Produce graphs for all conferences")
parser.add_argument("--sort", dest="sort", action="store_const", const=True, help="Sort the conferences.csv file.")

args = parser.parse_args()

if args.sort:
    full_conf_data = full_conf_data.sort_values(['Conference','Year', 'Sequence'])
    cols = full_conf_data.columns.tolist()
    cols = ['Conference','Year','Sequence','Accepted','Submitted']
    full_conf_data = full_conf_data[cols]
    full_conf_data.to_csv(filename,index=False)
    print(f"Sorted {filename}.")
    sys.exit(0)
    
if not args.conference_name and not args.all:
    parser.print_help()
    sys.exit(0)

conference_name_list = []
if args.conference_name:
    conference_name_list = [args.conference_name]
if args.all:
    conference_name_list = conference_list
    
for conference_name in conference_name_list:
    # Filter the data by conference
    conf_data = full_conf_data.copy()
    conf_data = conf_data.loc[conf_data["Conference"] == conference_name]

    print(conf_data)

    # Create a bar plot of acceptance rates by year
    #plt.bar(conf_data["Year"], conf_data["Papers accepted"] / conf_data["Papers submitted"])

    # Calculate the number of accepted and rejected papers for each year
    conf_data["Rejected"] = conf_data["Submitted"] - conf_data["Accepted"]
    conf_data["Acceptance Rate"] = conf_data["Accepted"] / conf_data["Submitted"] * 100 # Calculate the acceptance rate

    # Create a stacked bar plot of accepted and rejected papers by year
    plt.bar(conf_data["Year"], conf_data["Accepted"], color="green")
    plt.bar(conf_data["Year"], conf_data["Rejected"], bottom=conf_data["Accepted"], label="Rejected", color="red")

    # Set the x-axis label
    plt.xlabel("Year")

    # Set the y-axis label
    plt.ylabel("Accepted / Rejected Papers")

    # Set the title of the plot
    plt.title(f"{conference_name} Conference Publications by Year")

    # Save the plot
    plt.savefig(f"graphs/{conference_name}.png", bbox_inches="tight")
    plt.savefig(f"graphs/{conference_name}.pdf", bbox_inches="tight")

    plt.close()
