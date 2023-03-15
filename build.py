import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import PercentFormatter
import seaborn as sns
import sys

filename = "csconferences.csv"
URL = "https://github.com/emeryberger/csconferences"

areas_dict = {
    'AI': 'Artificial intelligence',
    'Vision': 'Computer vision',
    'ML': 'Machine learning',
    'NLP': 'Natural language processing',
    'Web+IR': 'The web & information retrieval',
    'Arch': 'Computer architecture',
    'Networks': 'Computer networks',
    'Security': 'Computer security',
    'DB': 'Databases',
    'Metrics' : 'Measurement & perf. analysis',
    'Mobile': 'Mobile computing',
    'OS': 'Operating systems',
    'PL': 'Programming languages',
    'SE': 'Software engineering',
    'Theory': 'Algorithms & complexity',
    'Logic': 'Logic & verification',
    'Crypt': 'Cryptography',
    'Graphics': 'Computer graphics',
    'HCI': 'Human-computer interaction',
}

def sort_areas(areas):
    return sorted(areas, key=lambda x: areas_dict[x]) # list(areas_dict.keys()).index(x) if x in areas_dict else float('inf'))

def get_human_readable_area(area):
    return areas_dict.get(area, area)

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
    full_conf_data = full_conf_data.sort_values(['Area','Conference','Year', 'Sequence', 'Source', 'Notes'])
    cols = full_conf_data.columns.tolist()
    cols = ['Area','Conference','Year','Sequence','Accepted','Submitted','Source','Notes']
    full_conf_data = full_conf_data[cols]
    full_conf_data = full_conf_data.drop_duplicates()
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

print('# csconferences.org\n')
print("## Computer Science Conference Publication Stats\n\n")

for conference_name in conference_name_list:

    plt.clf()
    fig = plt.figure()
    ax1 = fig.add_subplot()
    
    # Filter the data by conference
    conf_data = full_conf_data.copy()
    conf_data = conf_data.loc[conf_data["Conference"] == conference_name]

    this_area = conf_data["Area"].unique().tolist()[0]

    if this_area != previous_area:
        if previous_area != "":
            print("</details>\n")
            
        previous_area = this_area
        print("<details>")
        print("<summary>")
        print(f"<em>{this_area}</em>: <b>{get_human_readable_area(this_area)}</b>")
        print("</summary>")
        
    # print(f"![{conference_name}]({URL}/blob/main/graphs/{conference_name}.png)")
    print(f'<A NAME="{conference_name}">')
    print(f'<IMG SRC="{URL}/blob/main/graphs/{conference_name}.png?raw=true" WIDTH="500">')
    print('</A>')
    
    # Create a bar plot of acceptance rates by year
    #plt.bar(conf_data["Year"], conf_data["Papers accepted"] / conf_data["Papers submitted"])

    # Calculate the number of accepted and rejected papers for each year
    conf_data["Rejected"] = conf_data["Submitted"] - conf_data["Accepted"]
    conf_data["Acceptance Rate"] = 100 * conf_data["Accepted"] / conf_data["Submitted"] # Calculate the acceptance rate

    # Create a figure and two axes
    # fig, ax1 = plt.subplots()
    
    # Create a stacked bar plot of accepted and rejected papers by year
    ax1.bar(conf_data["Year"], conf_data["Rejected"], bottom=conf_data["Accepted"], label="Rejected", color="red")
    ax1.bar(conf_data["Year"], conf_data["Accepted"], color="green", label="Accepted")
    
    # Set the x-axis label
    # ax1.set_xlabel("Year")
    
    # Force integers on the x-axis
    years = conf_data["Year"].unique().tolist()
    ax1.set_xticks(evenly_spaced_items(years, 5))
    
    # Set the y-axis label for accepted/rejected papers
    # ax1.set_ylabel("Accepted / Rejected Papers")
    ax1.set_ylabel('Accepted / Rejected', color='black', fontsize=12)
    ax1.legend()
    
    # Create a second y-axis for acceptance rate
    ax2 = ax1.twinx()
    ax2.set_ylim([0, 100])
    ax2.plot(conf_data["Year"], conf_data["Acceptance Rate"], color="blue")
    ax2.set_ylabel("Acceptance Rate (%)", color='blue')
    ax2.yaxis.set_major_formatter(PercentFormatter())
    ax2.tick_params(axis='y',labelcolor='blue')
    # Show the legend
    # ax1.legend()

    # Set the title of the plot
    plt.title(f"{conference_name} Publications by Year", fontsize=16)

    # Save the plot
    plt.savefig(f"graphs/{conference_name}.pdf", bbox_inches="tight")
    plt.savefig(f"graphs/{conference_name}.png", bbox_inches="tight")

    plt.close()

print("</details>")

print("""

## Data sources

* Front matter in conference proceedings (primary source)
* [HotCRP.com](https://hotcrp.com)
* https://www.openresearch.org/wiki/
* https://people.engr.tamu.edu/guofei/sec_conf_stat.htm
* https://github.com/lixin4ever/Conference-Acceptance-Rate
* https://taniai.space/cvconf/
* https://unit.aist.go.jp/hcmrc/mr-rt/acceptance-rate.html
* Personal communications

## Notes on statistics

* When possible, total submitted papers excludes those rejected or withdrawn before review
* For conferences that make a distinction, these statistics include only "long" papers

## Other info

* All code and data for this site is at [https://github.com/emeryberger/csconferences](https://github.com/emeryberger/csconferences).
* For any corrections or updates, please make a pull request to the above site.
* To regenerate this page and all the graphs, run `python3 build.py --all > README.md` .
* This site was developed by and is maintained by [Emery Berger](https://github.com/emeryberger).
""")
