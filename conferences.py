import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import sys

filename = "conferences.csv"
URL = "https://github.com/emeryberger/conference-foo"

def evenly_spaced_items(lst, N):
    """
    Returns a new list with only N items, where the N items are evenly spaced in the original list.
    
    Args:
    lst (list): The original list of items.
    N (int): The number of items to include in the new list.
    
    Returns:
    A new list with only N items, where the N items are evenly spaced in the original list.
    """
    if N == 1:
        # Special case: return the middle item
        return [lst[len(lst)//2]]
    elif N >= len(lst):
        # Special case: return the original list
        return lst.copy()
    else:
        # Calculate the step size
        step = (len(lst) - 1) / (N - 1)
        
        # Create the new list
        new_lst = [lst[0]]
        for i in range(1, N-1):
            index = int(i * step)
            new_lst.append(lst[index])
        new_lst.append(lst[-1])
        
        return new_lst

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
    full_conf_data = full_conf_data.sort_values(['Area','Conference','Year', 'Sequence'])
    cols = full_conf_data.columns.tolist()
    cols = ['Area','Conference','Year','Sequence','Accepted','Submitted']
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

# Set the theme and remove the axes.
# sns.set_style("ticks")
sns.set_theme()
sns.despine()

# Set the dimensions (in inches) of the plot.
plt.figure(figsize=(3, 3))

previous_area = ""

# Do this once just to initialize everything.
plt.close()

# Combine the values for each year, conference, and area (since there may be different Sequence numbers).
full_conf_data = full_conf_data.groupby(['Year', 'Conference', 'Area']).agg({'Accepted': 'sum', 'Submitted': 'sum'}).reset_index()

for conference_name in conference_name_list:

    # Filter the data by conference
    conf_data = full_conf_data.copy()
    conf_data = conf_data.loc[conf_data["Conference"] == conference_name]

    this_area = conf_data["Area"].unique().tolist()[0]

    if this_area != previous_area:
        if previous_area != "":
            print("</details>\n")
            
        previous_area = this_area
        # print(f"\n### {this_area}\n")
        print("<details>")
        print("<summary>")
        print(f"{this_area}")
        print("</summary>")
        
    # print(f"![{conference_name}]({URL}/blob/main/graphs/{conference_name}.png)")
    print(f'<IMG SRC="{URL}/blob/main/graphs/{conference_name}.png" WIDTH="500"></IMG>')
    
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

    # Force integers on the x-axis
    years = conf_data["Year"].unique().tolist()
    plt.xticks(evenly_spaced_items(years, 5))
    
    # Set the y-axis label
    plt.ylabel("Accepted / Rejected Papers")

    # Set the title of the plot
    plt.title(f"{conference_name} Publications by Year")

    # Save the plot
    plt.savefig(f"graphs/{conference_name}.pdf", bbox_inches="tight")
    plt.savefig(f"graphs/{conference_name}.png", bbox_inches="tight")

    plt.close()

print("</details>")
