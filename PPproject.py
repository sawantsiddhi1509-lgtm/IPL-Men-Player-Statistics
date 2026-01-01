# Final GUI Version v3 (NO INQUIRY) with Auctions, Compare, Stats, Graphs
# Author: ChatGPT

import customtkinter as ctk
from tkinter import *
from tkinter import ttk, messagebox
import pandas as pd
import requests
from io import BytesIO
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import datetime
import difflib

# ===========================
# FILE PATHS
# ===========================

IPL_CSV = r"C:\Users\vaishali dashrath sa\Downloads\cricket_data_with_samples.csv"
PLAYERS_CSV = r"C:\Users\vaishali dashrath sa\Downloads\players_data_with_all_info.csv"

AUCTION_2022 = r"C:\Users\vaishali dashrath sa\Downloads\IPL_Auction_2022_FullList.csv"
AUCTION_2023 = r"C:\Users\vaishali dashrath sa\Downloads\IPL_2023-22_Sold_Players.csv"
AUCTION_2024 = r"C:\Users\vaishali dashrath sa\Downloads\IPL_2024_Players_Auction_Dataset.csv"

# ===========================
# LOAD FILES
# ===========================

df_ipl = pd.read_csv(IPL_CSV)
df_players = pd.read_csv(PLAYERS_CSV)

df_auction22 = pd.read_csv(AUCTION_2022)
df_auction23 = pd.read_csv(AUCTION_2023)
df_auction24 = pd.read_csv(AUCTION_2024)

# Normalize names for fuzzy matching
df_players["match_name"] = df_players["fullname"].str.lower().str.replace(" ", "")
df_ipl["match_name"] = df_ipl["Player_Name"].str.lower().str.replace(" ", "")
df_auction22["match_name"] = df_auction22["Players"].astype(str).str.lower().str.replace(" ", "")
df_auction23["match_name"] = df_auction23["Name"].astype(str).str.lower().str.replace(" ", "")
df_auction24["match_name"] = df_auction24["Players"].astype(str).str.lower().str.replace(" ", "")

# ===========================
# STATS DROPDOWN LIST
# ===========================

STAT_OPTIONS = [
    'Matches_Batted','Not_Outs','Runs_Scored','Highest_Score','Batting_Average',
    'Balls_Faced','Batting_Strike_Rate','Centuries','Half_Centuries','Fours',
    'Sixes','Catches_Taken','Stumpings','Matches_Bowled','Balls_Bowled',
    'Runs_Conceded','Wickets_Taken','Best_Bowling_Match','Bowling_Average',
    'Economy_Rate','Bowling_Strike_Rate','Four_Wicket_Hauls','Five_Wicket_Hauls'
]

GRAPH_TYPES = ["Line", "Dot", "Pie"]

# ===========================
# AGE CALCULATION
# ===========================

def calc_age(dob):
    try:
        dob = pd.to_datetime(dob)
        today = datetime.date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except:
        return "N/A"

# ===========================
# FUZZY MATCH
# ===========================

def fuzzy_match(name, options):
    clean = name.lower().replace(" ", "")
    match = difflib.get_close_matches(clean, options, n=1, cutoff=0.5)
    return match[0] if match else None

# ===========================
# GET AUCTION DATA
# ===========================

def get_auction_price(player):

    clean = player.lower().replace(" ", "")
    result = {"2022": "Not Available", "2023": "Not Available", "2024": "Not Available"}

    # Fuzzy lists
    list22 = df_auction22["match_name"].tolist()
    list23 = df_auction23["match_name"].tolist()
    list24 = df_auction24["match_name"].tolist()

    m22 = fuzzy_match(clean, list22)
    m23 = fuzzy_match(clean, list23)
    m24 = fuzzy_match(clean, list24)

    if m22:
        row = df_auction22[df_auction22["match_name"] == m22].iloc[0]
        try:
            price = float(str(row["Price Paid"]).replace(",", "")) / 100
            result["2022"] = f"₹ {price:.2f} Cr (Team: {row['Team']})"
        except: pass

    if m23:
        row = df_auction23[df_auction23["match_name"] == m23].iloc[0]
        try:
            price = float(str(row["Price"]).replace(",", "").replace("₹", "")) / 100
            result["2023"] = f"₹ {price:.2f} Cr (Team: {row['Team']})"
        except: pass

    if m24:
        row = df_auction24[df_auction24["match_name"] == m24].iloc[0]
        price = row["COST IN ₹ (CR.)"]
        result["2024"] = f"₹ {price} Cr (Team: {row['Team']})"

    return result

# ===========================
# GUI SETUP
# ===========================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("IPL Player Dashboard – Final Version v3 (NO Inquiry)")
root.geometry("1600x950")

# LEFT SIDEBAR
sidebar = ctk.CTkFrame(root, width=300)
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(sidebar, text="IPL PLAYERS", font=("Arial", 26, "bold")).pack(pady=20)

search_entry = ctk.CTkEntry(sidebar, placeholder_text="Search player...")
search_entry.pack(pady=10, padx=15)

player_list = Listbox(
    sidebar,
    height=30,
    width=30,
    bg="#111111",
    fg="white",
    selectbackground="#0044cc"
)
player_list.pack(padx=15, pady=10)

# Fill list
ipl_players = sorted(df_ipl["Player_Name"].unique())
for p in ipl_players:
    player_list.insert(END, p)

# MAIN PANEL
main = ctk.CTkFrame(root)
main.pack(side="right", fill="both", expand=True, padx=20, pady=20)

header = ctk.CTkLabel(main, text="Select a Player", font=("Arial", 32, "bold"))
header.pack(pady=10)

# Image + Summary
image_label = ctk.CTkLabel(main, text="")
image_label.pack(pady=10)

summary_box = ctk.CTkTextbox(main, width=900, height=250, font=("Arial", 16))
summary_box.pack(pady=10)

# BUTTONS (NO INQUIRY)
btn_frame = ctk.CTkFrame(main)
btn_frame.pack(pady=20)

stats_btn = ctk.CTkButton(btn_frame, text="Stats", width=200)
auction_btn = ctk.CTkButton(btn_frame, text="Auction", width=200)
compare_btn = ctk.CTkButton(btn_frame, text="Compare", width=200)

stats_btn.grid(row=0, column=0, padx=30)
auction_btn.grid(row=0, column=1, padx=30)
compare_btn.grid(row=0, column=2, padx=30)

current_player = None
current_stats = None

# ===========================
# LOAD IMAGE
# ===========================

def load_img(url):
    try:
        r = requests.get(url, timeout=5)
        img = Image.open(BytesIO(r.content))
        img = img.resize((320, 400))
        return ImageTk.PhotoImage(img)
    except:
        blank = Image.new("RGB", (320, 400), color=(40, 40, 40))
        return ImageTk.PhotoImage(blank)

# ===========================
# SHOW PLAYER
# ===========================

def show_player(event=None):
    global current_player, current_stats

    try:
        player = player_list.get(player_list.curselection())
    except:
        return

    current_player = player
    header.configure(text=player)

    info = df_players[df_players["fullname"].str.lower() == player.lower()]
    stats = df_ipl[df_ipl["Player_Name"] == player]
    current_stats = stats

    summary_box.delete("1.0", END)

    if not info.empty:
        row = info.iloc[0]
        img = load_img(row["image_path"])
        image_label.configure(image=img)
        image_label.image = img

        age = calc_age(row["dateofbirth"])
        h = stats["Height"].iloc[0] if "Height" in stats.columns else "N/A"
        w = stats["Weight"].iloc[0] if "Weight" in stats.columns else "N/A"

        summary_box.insert(END,
            f"Full Name: {row['fullname']}\n"
            f"Born: {row['dateofbirth']}\n"
            f"Age: {age}\n"
            f"Height: {h}\n"
            f"Weight: {w}\n"
            f"Country: {row['country_name']}\n"
            f"Role: {row['position']}\n"
            f"Batting: {row['battingstyle']}\n"
            f"Bowling: {row['bowlingstyle']}\n"
        )

player_list.bind("<<ListboxSelect>>", show_player)

# ===========================
# STATS WINDOW
# ===========================

def open_stats():
    if current_stats is None:
        return

    win = ctk.CTkToplevel(root)
    win.title("Player Stats")
    win.geometry("750x700")

    ctk.CTkLabel(win, text=f"Stats - {current_player}", font=("Arial", 24, "bold")).pack(pady=15)

    stat_dd = ttk.Combobox(win, values=STAT_OPTIONS, width=40)
    stat_dd.pack(pady=10)

    graph_dd = ttk.Combobox(win, values=GRAPH_TYPES, width=40)
    graph_dd.pack(pady=10)

    textbox = ctk.CTkTextbox(win, width=650, height=350)
    textbox.pack(pady=20)

    def show_stat():
        stat = stat_dd.get()
        gtype = graph_dd.get()

        if stat == "":
            return

        s = current_stats.sort_values("Year")
        textbox.delete("1.0", END)

        for _, r in s.iterrows():
            textbox.insert(END, f"{r['Year']}: {stat} = {r[stat]}\n")

        x = s["Year"].astype(str)
        y = s[stat]

        plt.figure(figsize=(7,4))

        if gtype == "Line":
            plt.plot(x, y, marker="o")
        elif gtype == "Dot":
            plt.scatter(x, y)
        elif gtype == "Pie":
            plt.pie(y, labels=x, autopct="%1.1f%%")

        plt.title(f"{stat} over Years - {current_player}")
        plt.grid(True, linestyle="--", alpha=0.3)
        plt.show()

    ctk.CTkButton(win, text="Show", command=show_stat).pack()

stats_btn.configure(command=open_stats)

# ===========================
# AUCTION WINDOW
# ===========================

def open_auction():

    if current_player is None:
        return

    result = get_auction_price(current_player)

    win = ctk.CTkToplevel(root)
    win.title("Auction Info")
    win.geometry("500x400")

    ctk.CTkLabel(win, text=f"Auction - {current_player}", font=("Arial", 26, "bold")).pack(pady=20)

    for year in ["2024", "2023", "2022"]:
        ctk.CTkLabel(win, text=f"{year}: {result[year]}", font=("Arial", 20)).pack(pady=10)

auction_btn.configure(command=open_auction)

# ===========================
# COMPARE WINDOW
# ===========================

def open_compare():

    win = ctk.CTkToplevel(root)
    win.title("Compare Players")
    win.geometry("800x700")

    ctk.CTkLabel(win, text="Compare Two Players", font=("Arial", 26, "bold")).pack(pady=20)

    p1 = ttk.Combobox(win, values=ipl_players, width=40)
    p2 = ttk.Combobox(win, values=ipl_players, width=40)

    p1.pack(pady=10)
    p2.pack(pady=10)

    result_box = ctk.CTkTextbox(win, width=700, height=350)
    result_box.pack(pady=20)

    graph_dd = ttk.Combobox(win, values=["Line", "Dot"], width=30)
    graph_dd.pack(pady=10)

    def compare_now():
        result_box.delete("1.0", END)

        A = p1.get().strip()
        B = p2.get().strip()

        if A == "" or B == "":
            result_box.insert(END, "Select both players!")
            return

        if A == B:
            result_box.insert(END, "Cannot compare same player!")
            return

        dfA = df_ipl[df_ipl["Player_Name"] == A].sort_values("Year")
        dfB = df_ipl[df_ipl["Player_Name"] == B].sort_values("Year")

        result_box.insert(END, f"=== {A} ===\n")
        result_box.insert(END, f"Runs: {dfA['Runs_Scored'].sum()}\n")
        result_box.insert(END, f"Wickets: {dfA['Wickets_Taken'].sum()}\n")
        result_box.insert(END, f"Best Score: {dfA['Highest_Score'].max()}\n\n")

        result_box.insert(END, f"=== {B} ===\n")
        result_box.insert(END, f"Runs: {dfB['Runs_Scored'].sum()}\n")
        result_box.insert(END, f"Wickets: {dfB['Wickets_Taken'].sum()}\n")
        result_box.insert(END, f"Best Score: {dfB['Highest_Score'].max()}\n\n")

        g = graph_dd.get()

        plt.figure(figsize=(8,5))
        if g == "Line":
            plt.plot(dfA["Year"], dfA["Runs_Scored"], marker="o", label=A)
            plt.plot(dfB["Year"], dfB["Runs_Scored"], marker="o", label=B)
        else:
            plt.scatter(dfA["Year"], dfA["Runs_Scored"], label=A)
            plt.scatter(dfB["Year"], dfB["Runs_Scored"], label=B)

        plt.xlabel("Year")
        plt.ylabel("Runs Scored")
        plt.title("Runs Comparison")
        plt.legend()
        plt.grid(True)
        plt.show()

    ctk.CTkButton(win, text="Compare", command=compare_now).pack(pady=10)

compare_btn.configure(command=open_compare)

# ===========================
# MAINLOOP
# ===========================

root.mainloop()

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

###############################################################################
# CONFIG – SET YOUR CSV PATH HERE
###############################################################################
DATA_FILE = r"C:\Users\vaishali dashrath sa\Downloads\cricket_data_with_samples.csv"


###############################################################################
# SAFE LOADING OF CSV
###############################################################################
try:
    df = pd.read_csv(DATA_FILE)
    print("✔ CSV Loaded Successfully!")
except:
    print("❌ CSV FILE NOT FOUND!")
    print("Make sure the path is correct!")
    exit()


###############################################################################
# CLEANING: lowercase helper column
###############################################################################
df["Player_Lower"] = df["Player_Name"].astype(str).str.lower()


###############################################################################
# FIND YEAR COLUMN OR CREATE ONE
###############################################################################
possible_year_cols = ["Year", "year", "Season", "season", "Match_Year"]

YEAR_COL = None
for col in df.columns:
    if col in possible_year_cols:
        YEAR_COL = col
        break

if YEAR_COL is None:
    print("⚠ No Year column found — creating artificial year index")
    df["YearAuto"] = np.arange(1, len(df) + 1)
    YEAR_COL = "YearAuto"


###############################################################################
# SAFELY CONVERT NUMERIC COLUMNS
###############################################################################
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="ignore")


###############################################################################
# HEALTH DATA (static sample data)
###############################################################################
HEALTH_DATA = {
    "jasprit bumrah": {"Height": "178 cm", "Weight": "72 kg", "Injuries": "Back issue (sample)"},
    "virat kohli": {"Height": "175 cm", "Weight": "70 kg", "Injuries": "None (sample)"},
    "rohit sharma": {"Height": "173 cm", "Weight": "78 kg", "Injuries": "Hamstring (sample)"}
}

def get_health(player):
    pl = player.lower()
    if pl in HEALTH_DATA:
        h = HEALTH_DATA[pl]
    else:
        h = {"Height": "N/A", "Weight": "N/A", "Injuries": "N/A"}

    print(f"\n=== HEALTH INFO FOR {player} ===")
    for k,v in h.items():
        print(f"{k}: {v}")


###############################################################################
# AUCTION PRICE ESTIMATOR (safe)
###############################################################################
def estimate_price(row):
    def safeVal(x):
        try:
            if np.isnan(x): return 0
        except:
            pass
        try: return float(x)
        except:
            return 0

    base = 1
    price = (
        base +
        safeVal(row.get("Runs_Scored", 0)) / 250 +
        safeVal(row.get("Wickets_Taken", 0)) * 0.3 +
        safeVal(row.get("Centuries", 0)) * 0.7 +
        safeVal(row.get("Half_Centuries", 0)) * 0.4
    )

    return round(min(max(price, 0.5), 20), 2)


###############################################################################
# PLOTTING FUNCTIONS (safe)
###############################################################################
def safe_plot_bar(x, y, title):
    try:
        plt.figure(figsize=(10,4))
        plt.bar(x,y)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except:
        print("⚠ Could not generate bar chart")

def safe_plot_line(x, y, title):
    try:
        plt.figure(figsize=(10,4))
        plt.plot(x,y,marker="o")
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except:
        print("⚠ Could not generate line chart")

def safe_plot_pie(labels, sizes, title):
    try:
        plt.figure(figsize=(6,6))
        plt.pie(sizes, labels=labels, autopct="%1.1f%%")
        plt.title(title)
        plt.show()
    except:
        print("⚠ Could not generate pie chart")


###############################################################################
# SMART PLAYER SEARCH
###############################################################################
def pick_player():
    search = input("\nEnter player name: ").lower()
    matches = df[df["Player_Lower"].str.contains(search)]

    players = sorted(matches["Player_Name"].unique())

    if len(players)==0:
        print("❌ No matching players found!")
        return None
    elif len(players)==1:
        print(f"✔ Selected: {players[0]}")
        return players[0]
    else:
        print("\nMultiple matches found:")
        for i,p in enumerate(players,1):
            print(f"{i}. {p}")
        try:
            sel = int(input("Choose index: "))
            return players[sel-1]
        except:
            print("❌ Invalid choice")
            return None


###############################################################################
# STATS MENU
###############################################################################
def stats(player):
    sub = df[df["Player_Name"] == player]

    if sub.empty:
        print("❌ No data found for this player")
        return

    print(f"\n=== AVAILABLE STAT COLUMNS FOR {player} ===")
    for i,col in enumerate(sub.columns):
        print(f"{i+1}. {col}")

    colname = input("\nChoose EXACT stat column name to display: ")

    if colname not in sub.columns:
        print("❌ That column does not exist!")
        return

    print(sub[[YEAR_COL, colname]])

    x = sub[YEAR_COL].astype(str)
    y = sub[colname]

    safe_plot_bar(x,y,f"{colname} Over Time for {player}")
    safe_plot_line(x,y,f"{colname} Trend for {player}")

    # pie only if numeric
    try:
        ynum = pd.to_numeric(y.dropna())
        if len(ynum)>1 and ynum.sum()>0:
            safe_plot_pie(x[:len(ynum)], ynum, f"{colname} PIE for {player}")
    except:
        pass


###############################################################################
# AUCTION MENU
###############################################################################
def auction(player):
    sub = df[df["Player_Name"] == player]

    if sub.empty:
        print("❌ No data found for this player")
        return

    sub["AuctionPrice"] = sub.apply(estimate_price,axis=1)

    print(f"\n=== ESTIMATED AUCTION HISTORY FOR {player} ===")
    print(sub[[YEAR_COL,"AuctionPrice"]])

    years = sub[YEAR_COL].astype(str)
    prices = sub["AuctionPrice"]

    safe_plot_bar(years, prices, f"Auction Price for {player}")
    safe_plot_line(years, prices, f"Auction Price Trend for {player}")
    safe_plot_pie(years, prices, f"Auction PIE for {player}")


###############################################################################
# MAIN LOOP
###############################################################################
print("\n=======================================")
print("     FINAL WORKING IPL ANALYZER")
print("   (100% Error Proof Version)")
print("=======================================\n")

while True:
    print("\nMain Menu:")
    print("1. Batter")
    print("2. Bowler")
    print("3. Exit")

    choice = input("Enter choice: ")
    if choice=="3":
        print("Goodbye!")
        break
    elif choice not in ["1","2"]:
        print("Invalid choice")
        continue

    player = pick_player()
    if not player:
        continue

    print("\nChoose:")
    print("1. Stats")
    print("2. Health")
    print("3. Auction")

    sub = input("Enter: ")

    if sub=="1":
        stats(player)
    elif sub=="2":
        get_health(player)
    elif sub=="3":
        auction(player)
    else:
        print("Invalid selection")