# Do not add complexity. Try to keep things simple. Implement all of the missing functions. Wrap all the code in ```python (markdown)
from matplotlib import pyplot as plt
import matplotlib
import matplotlib.patches as patches
import datetime
import re
from collections import defaultdict, Counter

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
    subjects = [
        "math",
        "geometry",
        "physics",
        "chemistry",
        "biology",
        "history",
        "geography",
        "literature|russian",
        "german",
        "social",
        "lw|lesswrong",
        "rss|surf",
        "anki|duolingo",
        "code|coding|programming",
        "writing",
        "telegram|tg",
        "youtube|yt",
        "statistics|probability",
    ]

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


def main():
    file_name = "/home/lyka/.worklog"  # Adjust file path as needed.
    records = get_records(file_name)

    # Uncomment the plots you want to generate:
    plot_days(records)
    plot_records(records)
    plot_work_time(records)
    plot_places(records)
    plot_subjects(records)

    # Example: Get records from the last 7 days and print how many:
    recent_records = last_n_days(records, 7)
    print(f"Records in the last 7 days: {len(recent_records)}")


if __name__ == "__main__":
    main()
