# Do not add complexity. Try to keep things simple. Implement all of the missing functions. Wrap all the code in ```python (markdown)
from matplotlib import pyplot as plt
import matplotlib
import matplotlib.patches as patches
import datetime
import re
from collections import defaultdict, Counter
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
import argparse

matplotlib.use("TkAgg")


class Record:
    def __init__(self, line):
        self.line = line.rstrip("\n")
        self.year = int(line[0:4])
        self.month = int(line[5:7])
        self.day = int(line[8:10])
        self.start_hour = int(line[11:13])
        self.start_min = int(line[14:16])  # It can only be 5, or 35. such are the rules.
        self.end_hour = int(line[17:19])
        self.end_min = int(line[20:22])  # It can only be 0, or 30, so every session is exactly 25 minutes.
        self.done = line[24] != " "
        self.location = line[27:29]
        self.description = line[30:]

        # Create a date object for easier handling
        self.date = datetime.date(self.year, self.month, self.day)

    def __str__(self):
        return self.line

    def __repr__(self):
        return self.line


def get_records(file_name):
    with open(file_name) as f:
        return [Record(line) for line in f if line.startswith("2")]  # Year 2000-3000 supported only


def plot_days(records):
    """Plot the number of records per day"""
    day_counts = defaultdict(int)
    for r in records:
        day_counts[r.date] += 1

    # sort days
    dates = sorted(day_counts.keys())
    counts = [day_counts[d] for d in dates]

    plt.figure(figsize=(10, 4))
    plt.bar([d.strftime("%Y-%m-%d") for d in dates], counts, color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Day")
    plt.ylabel("Number of Records")
    plt.title("Records per Day")
    plt.tight_layout()
    plt.show()


def plot_records(records):
    """
    Plot a GitHub-like table where the x-axis represents half-hour time slots
    in a day (from 0 to 47) and the y-axis represents different days.
    A colored rectangle indicates a record at that time slot. Blue if done, red if not.
    """
    # Get list of unique days in sorted order
    unique_days = sorted({r.date for r in records})
    day_index = {day: i for i, day in enumerate(unique_days)}

    # Setup plot
    fig, ax = plt.subplots(figsize=(12, len(unique_days) * 0.3 + 2))

    # For each record, calculate time slot index: each cell equals a half-hour.
    # We'll place a rectangle at (slot, day_index)
    for r in records:
        slot = r.start_hour * 2 + (r.start_min // 30)
        color = "blue" if r.done else "red"
        y = day_index[r.date]  # vertical position
        # draw rectangle: width=1, height=1
        rect = patches.Rectangle((slot, y), 1, 1, facecolor=color, edgecolor="none")
        ax.add_patch(rect)
        # Optionally add location text if desired, centered in cell:
        ax.text(slot + 0.5, y + 0.5, r.location.strip(), ha="center", va="center", fontsize=6, color="white")

    # Set limits and labels
    ax.set_xlim(0, 48)  # 48 half-hour slots in a day
    ax.set_ylim(0, len(unique_days))
    ax.set_xticks(range(0, 49, 2))
    ax.set_xticklabels([f"{h}:00" for h in range(0, 25)])
    ax.set_yticks([i + 0.5 for i in range(len(unique_days))])
    ax.set_yticklabels([d.strftime("%Y-%m-%d") for d in unique_days])
    ax.set_xlabel("Time of Day")
    ax.set_ylabel("Day")
    ax.set_title("Records Timeline (Blue = done, Red = not done)")
    plt.tight_layout()
    plt.show()


def plot_work_time(records):
    """
    Plot average number of records during each hour of the day.
    For each record, we use its start_hour as the bucket.
    """
    hour_counts = defaultdict(int)
    # Count records per hour
    for r in records:
        hour_counts[r.start_hour] += 1

    # Determine how many unique days exist in records.
    unique_days = {r.date for r in records}
    num_days = len(unique_days) if unique_days else 1

    # Calculate average (records happening during that hour per day).
    hours = list(range(24))
    averages = [hour_counts.get(h, 0) / num_days for h in hours]

    plt.figure(figsize=(10, 4))
    plt.bar(hours, averages, color="green")
    plt.xlabel("Hour of Day")
    plt.ylabel("Average Number of Records")
    plt.title("Average Records per Hour (across days)")
    plt.xticks(hours)
    plt.tight_layout()
    plt.show()


def plot_places(records):
    """Plot number of records per location (places) as a bar chart."""
    place_counts = Counter(r.location.strip() for r in records if r.location.strip())
    places = list(place_counts.keys())
    counts = list(place_counts.values())

    plt.figure(figsize=(8, 4))
    plt.bar(places, counts, color="orange")
    plt.xlabel("Location")
    plt.ylabel("Number of Records")
    plt.title("Records per Place")
    plt.tight_layout()
    plt.show()


def plot_subjects(records):
    """
    Plot number of records per subject.
    For each record, assign it to the first matching subject based on its description.
    Matching is case-insensitive and subject entry may have multiple alternatives separated by |.
    Records that do not match any subject are counted under 'other'.
    """
    with open("subjects") as f:
        subjects = f.read().splitlines()

    subject_counts = defaultdict(int)

    for r in records:
        desc = r.description.lower()
        matched = False
        for subj_pattern in subjects:
            # Create a regex pattern from subject pattern groups
            pattern = r"\b(?:" + subj_pattern + r")\b"
            if re.search(pattern, desc, re.IGNORECASE):
                subject_counts[subj_pattern] += 1
                matched = True
                break
        if not matched:
            subject_counts["other"] += 1

    # Prepare data for plotting.
    keys = list(subject_counts.keys())
    values = list(subject_counts.values())

    plt.figure(figsize=(10, 4))
    plt.bar(keys, values, color="purple")
    plt.xlabel("Subject")
    plt.ylabel("Number of Records")
    plt.title("Records per Subject")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()


def plot_habits(records):
    """Make GitHub-like habit tracker for all the habits mentioned in habits file"""
    # Read habits from the file
    with open("habits") as f:
        habits_list = [line.strip() for line in f if line.strip()]

    # Handle case with no records
    if not records:
        print("No records to plot.")
        return

    # Determine all days in the range from min to max date
    min_date = min(r.date for r in records)
    max_date = max(r.date for r in records)
    all_days = [min_date + datetime.timedelta(days=i) for i in range((max_date - min_date).days + 1)]

    # Group records by day for efficiency
    records_by_day = defaultdict(list)
    for r in records:
        records_by_day[r.date].append(r)

    # Build a 2D array: rows = habits, columns = days
    habits_data = []
    for habit in habits_list:
        # Create regex pattern for habit keywords (e.g., "exercise|workout")
        pattern = r"\b(?:" + habit + r")\b"
        row = []
        for day in all_days:
            day_records = records_by_day[day]
            # Check if any record description matches the habit pattern
            performed = (
                any(re.search(pattern, r.description, re.IGNORECASE) for r in day_records) if day_records else False
            )
            row.append(1 if performed else 0)
        habits_data.append(row)

    # Convert to numpy array for easier handling
    habits_array = np.array(habits_data)

    # Define cell size and gap size
    cell_size = 0.4  # Size of each cell in inches (adjust as needed)
    gap_size = 0.05  # Gap between cells in inches (adjust as needed)

    # Calculate total width and height including gaps
    num_days = len(all_days)
    num_habits = len(habits_list)
    total_width = num_days * (cell_size + gap_size) + gap_size
    total_height = num_habits * (cell_size + gap_size) + gap_size

    # Create the plot
    fig, ax = plt.subplots(figsize=(total_width, total_height))

    # Draw rectangles for each cell
    for i in range(num_habits):  # Rows (habits)
        for j in range(num_days):  # Columns (days)
            color = "green" if habits_array[i, j] == 1 else "white"
            # Calculate position with gaps
            x = j * (cell_size + gap_size) + gap_size
            y = (num_habits - 1 - i) * (cell_size + gap_size) + gap_size  # Invert y-axis so first habit is at top
            rect = Rectangle((x, y), cell_size, cell_size, facecolor=color, edgecolor="gray", linewidth=0.5)
            ax.add_patch(rect)

    # Set axis limits
    ax.set_xlim(0, total_width)
    ax.set_ylim(0, total_height)

    # Set y-axis ticks and labels (habits)
    ax.set_yticks([i * (cell_size + gap_size) + cell_size / 2 for i in range(num_habits)])
    ax.set_yticklabels(habits_list[::-1])  # Reverse to match top-to-bottom order

    # Set x-axis ticks and labels (days, approximately 10 ticks)
    tick_interval = max(1, num_days // 10)
    tick_positions = [j * (cell_size + gap_size) + cell_size / 2 for j in range(0, num_days, tick_interval)]
    tick_labels = [all_days[j].strftime("%Y-%m-%d") for j in range(0, num_days, tick_interval)]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")

    # Add labels and title
    ax.set_xlabel("Day")
    ax.set_ylabel("Habit")
    ax.set_title("Habit Tracker")

    # Remove default grid or background
    # ax.set_facecolor("white")
    # plt.tight_layout()
    plt.show()


def last_n_days(records, n):
    """Return only records from the last n days.

    Determined by the maximum date in records.
    """
    if not records:
        return []
    # Determine the latest date
    latest_date = max(r.date for r in records)
    threshold = latest_date - datetime.timedelta(days=n - 1)
    return [r for r in records if r.date >= threshold]


def plot_all(records):
    plot_habits(records)
    plot_days(records)
    plot_records(records)
    plot_work_time(records)
    plot_places(records)
    plot_subjects(records)


def main():
    parser = argparse.ArgumentParser(description="Generate plots from a worklog file.")
    parser.add_argument(
        "plot_type",
        choices=["days", "records", "work_time", "places", "subjects", "habits", "all"],
        default="all",
        help="Type of plot to generate",
    )
    parser.add_argument(
        "--file", default="/home/lyka/.worklog", help="Path to the worklog file (default: /home/lyka/.worklog)"
    )
    args = parser.parse_args()
    records = get_records(args.file)
    plot_functions = {
        "days": plot_days,
        "records": plot_records,
        "work_time": plot_work_time,
        "places": plot_places,
        "subjects": plot_subjects,
        "habits": plot_habits,
        "all": plot_all,
    }
    if args.plot_type in plot_functions:
        plot_functions[args.plot_type](records)
    else:
        print(f"Unknown plot type: {args.plot_type}. Use one of: {', '.join(plot_functions.keys())}")


if __name__ == "__main__":
    main()
