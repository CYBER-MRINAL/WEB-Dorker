#!/usr/bin/env python3

# Author: CYBER-MRINAL
# GitHub: CYBER-MRINAL
# Purpose: Professional multi-engine dorking tool (ethical use only)

import webbrowser
import os
import glob
import csv
import json
import urllib.parse
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

LOG_DIR = "dork_logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ===============================
# 60 Verified Professional Templates (6 categories x 10 each)
# ===============================
templates = {
    1: ("Directory & Index Exposure", [
        "site:{} intitle:\"index of /\" \"parent directory\"",
        "site:{} intitle:\"index of /admin\"",
        "site:{} intitle:\"index of /config\"",
        "site:{} intitle:\"index of /backup\"",
        "site:{} \"index of\" \"database.sql\"",
        "site:{} \"index of\" \"wp-content/uploads\"",
        "site:{} \"index of\" passwd",
        "site:{} \"index of\" etc/shadow",
        "site:{} \"index of\" *.bak",
        "site:{} \"index of\" *.git",
    ]),

    2: ("Login Pages", [
        "site:{} inurl:login",
        "site:{} inurl:admin",
        "site:{} inurl:wp-login.php",
        "site:{} inurl:cgi-bin/login",
        "site:{} intitle:\"admin login\"",
        "site:{} \"login\" \"Username\" \"Password\"",
        "site:{} inurl:signin",
        "site:{} inurl:logon",
        "site:{} intitle:\"Control Panel Login\"",
        "site:{} inurl:auth",
    ]),

    3: ("Sensitive Files", [
        "site:{} filetype:env \"DB_PASSWORD\"",
        "site:{} filetype:sql \"INSERT INTO\"",
        "site:{} filetype:bak inurl:/",
        "site:{} filetype:cfg inurl:/",
        "site:{} filetype:json \"api_key\"",
        "site:{} filetype:xml \"password\"",
        "site:{} filetype:log \"ERROR\"",
        "site:{} filetype:conf inurl:/",
        "site:{} filetype:txt \"password\"",
        "site:{} filetype:xls \"password\"",
    ]),

    4: ("Vulnerable Applications (common params)", [
        "site:{} inurl:php?id=",
        "site:{} inurl:index.php?id=",
        "site:{} inurl:catid=",
        "site:{} inurl:pageid=",
        "site:{} inurl:product.php?id=",
        "site:{} inurl:shop.php?pid=",
        "site:{} inurl:download.php?file=",
        "site:{} inurl:view.php?id=",
        "site:{} inurl:news.php?id=",
        "site:{} inurl:article.php?id=",
    ]),

    5: ("Cloud & Credentials Exposure", [
        "site:{} inurl:.aws/credentials",
        "site:{} inurl:.git/config",
        "site:{} inurl:.svn/entries",
        "site:{} inurl:.docker/config.json",
        "site:{} filetype:json \"auth_token\"",
        "site:{} filetype:yml \"secret\"",
        "site:{} \"PRIVATE KEY\" filetype:pem",
        "site:{} \"BEGIN RSA PRIVATE KEY\"",
        "site:{} \"ssh-rsa\" \"PRIVATE\"",
        "site:{} filetype:ppk \"private\"",
    ]),

    6: ("Cameras & IoT", [
        "site:{} inurl:view/view.shtml",
        "site:{} inurl:viewer/live/en",
        "site:{} intitle:\"webcamXP\"",
        "site:{} intitle:\"Live View / - AXIS\"",
        "site:{} inurl:8080/view.shtml",
        "site:{} intitle:\"NetCam Live Image\"",
        "site:{} intitle:\"IP Camera\" inurl:view",
        "site:{} \"webcam 7\" intitle:\"Live\"",
        "site:{} intitle:\"live view\" inurl:cam",
        "site:{} inurl:/video.mjpg",
    ]),
}

# ===============================
# Utilities
# ===============================

def _timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _ensure_session_files(target):
    """Create timestamped session log files and return their paths."""
    ts = _timestamp()
    base = f"dorks_{target}_{ts}"
    txt = os.path.join(LOG_DIR, base + ".txt")
    js = os.path.join(LOG_DIR, base + ".jsonl")
    csvf = os.path.join(LOG_DIR, base + ".csv")

    # create CSV with header
    if not os.path.exists(csvf):
        with open(csvf, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "engine", "query", "url"])

    return txt, js, csvf


def _url_for(engine, query):
    encoded = urllib.parse.quote_plus(query)
    if engine == "google":
        return f"https://www.google.com/search?q={encoded}"
    if engine == "bing":
        return f"https://www.bing.com/search?q={encoded}"
    if engine == "duckduckgo":
        return f"https://duckduckgo.com/?q={encoded}"
    # default
    return f"https://www.google.com/search?q={encoded}"


def _log_entry(txt_path, jsonl_path, csv_path, engine, query, url):
    entry = {"timestamp": _timestamp(), "engine": engine, "query": query, "url": url}
    # append text
    with open(txt_path, "a", encoding="utf-8") as f:
        f.write(f"[{entry['timestamp']}] [{engine}] {query} -> {url}\n")
    # append jsonl
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    # append csv
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([entry['timestamp'], engine, query, url])


def _print_two_columns(items, start_index=1, width=40):
    # prints items (list of strings) in two columns with indices
    left_col = items[0::2]
    right_col = items[1::2]
    max_len = max(len(left_col), len(right_col))
    for i in range(max_len):
        left_idx = start_index + i * 2
        left = f"[{left_idx}] {left_col[i] if i < len(left_col) else ''}".ljust(width)
        right = ""
        if i < len(right_col):
            right_idx = left_idx + 1
            right = f"[{right_idx}] {right_col[i]}"
        print(Fore.GREEN + left + right)


def _parse_numbers(selection, max_n):
    """Parse a selection like 'all' or '1,2,5' into a list of indices (1-based)."""
    selection = selection.strip().lower()
    if selection in ("all", "a", "*"):
        return list(range(1, max_n + 1))
    parts = [p.strip() for p in selection.split(",") if p.strip()]
    nums = []
    for p in parts:
        if "-" in p:
            try:
                a, b = p.split("-", 1)
                a = int(a); b = int(b)
                if a <= b:
                    nums.extend(list(range(a, b + 1)))
            except Exception:
                continue
        else:
            try:
                n = int(p)
                nums.append(n)
            except Exception:
                continue
    # filter
    nums = sorted(set([n for n in nums if 1 <= n <= max_n]))
    return nums


# ===============================
# History browsing
# ===============================

def history_mode():
    logs = sorted(glob.glob(os.path.join(LOG_DIR, "dorks_*.txt")), reverse=True)
    if not logs:
        print(Fore.RED + "\n[!] No logs found.")
        return
    print(Fore.CYAN + "\nAvailable log files:")
    for i, path in enumerate(logs, 1):
        print(Fore.GREEN + f"[{i}] {os.path.basename(path)}")
    choice = input(Fore.YELLOW + "\nEnter log number to view (or 0 to cancel): ")
    try:
        idx = int(choice)
        if idx == 0:
            return
        sel = logs[idx - 1]
    except Exception:
        print(Fore.RED + "Invalid choice")
        return

    with open(sel, "r", encoding="utf-8") as f:
        print(Fore.CYAN + f"\n--- Contents of {os.path.basename(sel)} ---\n")
        print(f.read())
    open_in_browser = input(Fore.YELLOW + "Open all queries in browser? (y/N): ").strip().lower()
    if open_in_browser == "y":
        # read JSONL to get queries (safer)
        jsonl = sel.rsplit('.', 1)[0] + '.jsonl'
        if os.path.exists(jsonl):
            with open(jsonl, 'r', encoding='utf-8') as jf:
                for line in jf:
                    try:
                        e = json.loads(line)
                        webbrowser.open(e.get('url'), new=2)
                    except Exception:
                        continue
        else:
            print(Fore.RED + "No jsonl file found for URLs. Cannot open automatically.")


# ===============================
# Core interactive generator
# ===============================

def interactive_session():
    print(Fore.CYAN + "\n=== Advanced Multi-Engine Dorking Tool (Professional) ===")
    print(Fore.MAGENTA + "     Options: H=History  Q=Quit  C=Custom dork\n")

    while True:
        target = input(Fore.YELLOW + " Enter (domain) or (option):> ").strip()
        if not target:
            continue
        if target.lower() == 'q':
            print(Fore.CYAN + " [^_^] Exiting (see you soon)...")
            return
        if target.lower() == 'h':
            history_mode()
            continue
        if target.lower() == 'c':
            custom_mode()
            continue

        # Choose engine once per session target
        engine = _choose_engine()

        # Choose categories
        print(Fore.CYAN + "\nAvailable categories:")
        cats = [templates[k][0] for k in sorted(templates.keys())]
        _print_two_columns(cats, start_index=1)
        print(Fore.YELLOW + "\nYou can select 1 or multiple categories separated by commas (e.g. 1,3) or 'all'.")
        sel = input(Fore.YELLOW + " Choose categories:> ").strip()
        if not sel:
            continue
        # map chosen indices to dorks
        if sel.lower() in ('all', 'a', '*'):
            chosen_keys = sorted(templates.keys())
        else:
            try:
                parts = [int(x.strip()) for x in sel.split(',') if x.strip()]
                chosen_keys = [sorted(templates.keys())[p - 1] for p in parts if 1 <= p <= len(templates)]
            except Exception:
                print(Fore.RED + "Invalid category selection")
                continue

        # aggregate dorks
        aggregated = []
        cat_names = []
        for k in chosen_keys:
            cat_names.append(templates[k][0])
            aggregated.extend(templates[k][1])

        if not aggregated:
            print(Fore.RED + "No dorks found for selected categories.")
            continue

        # show aggregated dorks in two columns
        print(Fore.CYAN + "\nAggregated dorks:")
        _print_two_columns(aggregated, start_index=1)

        # choose dorks to run
        print(Fore.YELLOW + "\nEnter dork numbers to run (e.g. 1,3-5) or 'all':")
        nums = input(Fore.YELLOW + "Dork selection: ").strip()
        if not nums:
            continue
        indices = _parse_numbers(nums, len(aggregated))
        if not indices:
            print(Fore.RED + "No valid dork indices selected.")
            continue

        # prepare session files
        txt_path, jsonl_path, csv_path = _ensure_session_files(target.replace('.', '_'))

        # save the generated dork list (txt + json)
        save_generated_dorks(target, aggregated, cat_names)

        # confirm and open
        confirm = input(Fore.YELLOW + f"Open {len(indices)} queries in {engine}? (y/N): ").strip().lower()
        if confirm != 'y':
            print(Fore.CYAN + "Cancelled by user.")
            continue

        for idx in indices:
            q = aggregated[idx - 1]
            query = q.format(target)
            url = _url_for(engine, query)
            webbrowser.open(url, new=2)
            _log_entry(txt_path, jsonl_path, csv_path, engine, query, url)

        print(Fore.GREEN + f"[+] Completed opening {len(indices)} queries. Logs saved in {LOG_DIR}.")


# ===============================
# Custom mode
# ===============================

def custom_mode():
    print(Fore.CYAN + "\n=== Custom Dork Mode ===")
    engine = _choose_engine()
    target = input(Fore.YELLOW + "Target domain to format into dork (leave blank for global): ").strip()
    print(Fore.YELLOW + "Enter custom dorks one per line. Use {} as placeholder for site. Type 'done' when finished.")
    custom = []
    while True:
        line = input(Fore.GREEN + "> ").rstrip('\n')
        if not line:
            continue
        if line.lower() == 'done':
            break
        custom.append(line.format(target) if '{}' in line and target else line)

    if not custom:
        print(Fore.RED + "No custom dorks entered.")
        return

    # prepare session files
    txt_path, jsonl_path, csv_path = _ensure_session_files((target or 'global').replace('.', '_'))

    print(Fore.CYAN + "\nCustom dorks to run:")
    for i, c in enumerate(custom, 1):
        print(Fore.GREEN + f"[{i}] {c}")

    confirm = input(Fore.YELLOW + f"Open all {len(custom)} custom queries in {engine}? (y/N): ").strip().lower()
    if confirm != 'y':
        print(Fore.CYAN + "Cancelled by user.")
        return

    for c in custom:
        query = c
        url = _url_for(engine, query)
        webbrowser.open(url, new=2)
        _log_entry(txt_path, jsonl_path, csv_path, engine, query, url)

    print(Fore.GREEN + f"[+] Completed opening {len(custom)} custom queries. Logs saved in {LOG_DIR}.")


# ===============================
# Helpers continued
# ===============================

def _choose_engine():
    print(Fore.CYAN + "\nChoose search engine:")
    print(Fore.GREEN + "[1] Google  [2] Bing  [3] DuckDuckGo")
    echoice = input(Fore.YELLOW + " Engine (1/2/3, default 1):> ").strip()
    if echoice == '2':
        return 'bing'
    if echoice == '3':
        return 'duckduckgo'
    return 'google'


def save_generated_dorks(target, dorks, categories):
    """Save the aggregated generated dorks for later review."""
    ts = _timestamp()
    base = f"generated_{target.replace('.', '_')}_{ts}"
    txt = os.path.join(LOG_DIR, base + ".txt")
    js = os.path.join(LOG_DIR, base + ".json")

    with open(txt, 'w', encoding='utf-8') as f:
        for d in dorks:
            f.write(d + "\n")

    with open(js, 'w', encoding='utf-8') as f:
        json.dump({"target": target, "categories": categories, "dorks": dorks}, f, indent=2)

    print(Fore.CYAN + f"[+] Saved generated dorks to {txt} and {js}")


# ===============================
# Entry point
# ===============================

if __name__ == '__main__':
    interactive_session()

