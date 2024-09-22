import os
import zipfile
import sqlite3
import subprocess
import struct
import logging
import requests
import shutil
import py7zr
from collections import defaultdict

def setup_logging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create handlers: one for console and one for file
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('file_processing.log')

    # Set logging levels
    console_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)

    # Create a formatter and set it for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# Setup logging once at the start of the script
setup_logging()

# Path configurations
archive_folder = "games"
database_file = "file_processing_log.sqlite"
dolphin_tool_path = "DolphinTool.exe"
wit_tool_path = "wit.exe"
wiitdb_file_path = "wiitdb.txt"  # Path to the wiitdb.txt file

if not os.path.exists(dolphin_tool_path):
    logging.error("DolphinTool.exe not found.")
    url = "https://dl.dolphin-emu.org/releases/2409/dolphin-2409-x64.7z"
    logging.info(f"Downloading DolphinTool.exe from {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    logging.info(f"Response: {response.status_code}")
    with open("dolphin.7z", 'wb') as f:
        f.write(response.content)
    logging.info(f"Saved dolphin.7z")
    with py7zr.SevenZipFile("dolphin.7z", mode='r') as z:
        z.extractall("dolphin")
    os.remove("dolphin.7z")
    logging.info(f"Extracted dolphin.7z to dolphin folder")
    for root, dirs, files in os.walk("dolphin"):
        for file in files:
            if file == "DolphinTool.exe":
                os.rename(os.path.join(root, file), dolphin_tool_path)
                logging.info(f"Moved DolphinTool.exe to root folder")
    shutil.rmtree("dolphin")
    logging.info(f"Deleted dolphin folder")
    logging.info(f"Saved DolphinTool.exe to {dolphin_tool_path}")

if not os.path.exists(wit_tool_path):
    logging.error("wit.exe not found.")
    url = "https://wit.wiimm.de/download/wit-v3.05a-r8638-cygwin64.zip"
    logging.info(f"Downloading wit.exe from {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    logging.info(f"Response: {response.status_code}")
    with open("wit.zip", 'wb') as f:
        f.write(response.content)
    logging.info(f"Saved wit.zip")
    with zipfile.ZipFile("wit.zip", 'r') as zip_ref:
        zip_ref.extractall("wit")
    os.remove("wit.zip")
    logging.info(f"Extracted wit.zip to wit folder")
    for root, dirs, files in os.walk("wit"):
        for file in files:
            if file == "wit.exe":
                os.rename(os.path.join(root, file), wit_tool_path)
                logging.info(f"Moved wit.exe to root folder")
    shutil.rmtree("wit")
    logging.info(f"Deleted wit folder")
    logging.info(f"Saved wit.exe to {wit_tool_path}")

if not os.path.exists(wiitdb_file_path):
    logging.error("wiitdb.txt not found.")
    url = "https://www.gametdb.com/wiitdb.txt?LANG=ORIG"
    logging.info(f"Downloading wiitdb.txt from {url}")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    logging.info(f"Response: {response.status_code}")
    with open(wiitdb_file_path, 'wb') as f:
        f.write(response.content)
    logging.info(f"Saved wiitdb.txt to {wiitdb_file_path}")

# Initialize SQLite Database and create tables
def initialize_database():
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    
    # Create the process_log table to log the overall process
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zip_file TEXT,
            unzipped_folder TEXT,
            rvz_file TEXT,
            iso_file TEXT,
            wbfs_file TEXT,
            region TEXT,
            status TEXT,
            error_message TEXT
        )
    ''')
    
    # Create the duplicate_games table to log games found in multiple regions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duplicate_games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_identifier TEXT,
            game_id TEXT,
            region TEXT,
            game_name TEXT,
            file_path TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Get all zip files from archive
def get_zip_files():
    zip_files = []
    for root, dirs, files in os.walk(archive_folder):
        for file in files:
            if file.endswith(".zip"):
                zip_files.append(os.path.join(root, file))
    return zip_files

# Log entry in the process_log table
def log_process(zip_file, unzipped_folder, rvz_file, iso_file, wbfs_file, region, status, error_message=None):
    logging.info(f"Processing {zip_file} - {status}")
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO process_log (zip_file, unzipped_folder, rvz_file, iso_file, wbfs_file, region, status, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (zip_file, unzipped_folder, rvz_file, iso_file, wbfs_file, region, status, error_message))
    conn.commit()
    conn.close()

# Log duplicate game entries into duplicate_games table, including file paths and game names
def log_duplicate_game(game_identifier, game_id, region, game_name, file_path):
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO duplicate_games (game_identifier, game_id, region, game_name, file_path)
        VALUES (?, ?, ?, ?, ?)
    ''', (game_identifier, game_id, region, game_name, file_path))
    conn.commit()
    conn.close()

# Unzip file and return unzipped folder path
def unzip_file(zip_file):
    try:
        unzipped_folder = zip_file[:-4]  # Remove '.zip'
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(unzipped_folder)
        os.remove(zip_file)  # Delete zip file after extraction
        return unzipped_folder
    except Exception as e:
        log_process(zip_file, None, None, None, None, None, "Failed", str(e))
        raise

# Parse wiitdb.txt to create a lookup dictionary for game regions and names
def parse_wiitdb():
    game_db = {}
    try:
        with open(wiitdb_file_path, 'r', encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:  # Ensure it's a valid entry
                    game_id, game_name = line.split('=', 1)  # Split Game ID and title
                    game_id = game_id.strip().upper()  # Clean up Game ID
                    game_name = game_name.strip()  # Clean up Game Name
                    
                    # Determine the region based on the fourth character of the Game ID
                    region_code = game_id[3]
                    if region_code == 'E':
                        region = "US"
                    elif region_code == 'P':
                        region = "EU"
                    elif region_code == 'J':
                        region = "JP"
                    else:
                        region = "Unknown"
                    
                    # Add the game ID, region, and game name to the dictionary
                    game_db[game_id] = {'region': region, 'game_name': game_name}
    except Exception as e:
        print(e)
        logging.error(f"Failed to parse wiitdb.txt: {e}")
    
    return game_db

# Find the region and game name from the game ID using the parsed wiitdb dictionary
def find_game_info(game_id, wiitdb):
    game_id = game_id.strip().upper()  # Ensure Game ID is uppercase and stripped of whitespace
    return wiitdb.get(game_id, {'region': "Unknown", 'game_name': "Unknown"})  # Use the Game ID to find the region and name

# Extract the Game ID from the first 6 bytes of the .iso file
def extract_game_id(file_path):
    try:
        with open(file_path, 'rb') as f:
            game_id = f.read(6).decode('ascii')  # The first 6 bytes represent the Game ID
        return game_id
    except Exception as e:
        logging.error(f"Failed to extract Game ID from {file_path}: {e}")
        return None

# Convert RVZ to ISO using DolphinTool
def convert_rvz_to_iso(rvz_file, output_folder):
    try:
        iso_file = os.path.join(output_folder, os.path.basename(rvz_file).replace(".rvz", ".iso"))
        command = f'{dolphin_tool_path} convert -i "{rvz_file}" -o "{iso_file}" -f iso'
        subprocess.run(command, check=True, shell=True)
        return iso_file
    except subprocess.CalledProcessError as e:
        log_process(None, None, rvz_file, None, None, None, "Failed", str(e))
        raise

# Convert ISO to WBFS using wit and delete ISO after successful conversion
def convert_iso_to_wbfs(iso_file, output_folder):
    try:
        wbfs_file = os.path.join(output_folder, os.path.basename(iso_file).replace(".iso", ".wbfs"))
        command = f'{wit_tool_path} COPY "{iso_file}" "{wbfs_file}" -P -B'
        subprocess.run(command, check=True, shell=True)
        os.remove(iso_file)
        return wbfs_file
    except subprocess.CalledProcessError as e:
        log_process(None, None, None, iso_file, None, None, "Failed", str(e))
        raise
    except Exception as e:
        log_process(None, None, None, iso_file, None, None, "Failed", str(e))
        raise

# Group games by their unique identifier and check for different regions
def find_duplicate_games_in_diff_regions(archive_games):
    grouped_games = defaultdict(list)
    
    # Group games by their unique identifier (first 3 characters of Game ID)
    for game_id, info in archive_games.items():
        game_identifier = game_id[:3]  # First 3 characters of the Game ID
        grouped_games[game_identifier].append((game_id, info['region'], info['game_name'], info['file_path']))
    
    # Check for games that exist in multiple regions
    duplicates = {}
    for game_identifier, games in grouped_games.items():
        if len(games) > 1:  # More than one version of the game exists
            duplicates[game_identifier] = games
            # Log duplicate games into the database
            for game_id, region, game_name, file_path in games:
                log_duplicate_game(game_identifier, game_id, region, game_name, file_path)
    
    return duplicates

# Process all the zip files, convert, log, and then check for region duplicates
def process_files():
    initialize_database()
    zip_files = get_zip_files()

    # Parse wiitdb.txt to build game region and name lookup
    wiitdb = parse_wiitdb()

    archive_games = {}

    for zip_file in zip_files:
        try:
            # Step 1: Unzip the file
            unzipped_folder = unzip_file(zip_file)
            logging.info(f"Unzipped {zip_file} to {unzipped_folder}")
            
            # Step 2: Find the .rvz file
            rvz_file = None
            for root, dirs, files in os.walk(unzipped_folder):
                for file in files:
                    if file.endswith(".rvz"):
                        rvz_file = os.path.join(root, file)
                        break
            if not rvz_file:
                raise Exception("No .rvz file found in the unzipped folder.")
            
            # Step 3: Convert .rvz to .iso to extract Game ID
            logging.info(f"Converting {rvz_file} to .iso")
            iso_file = convert_rvz_to_iso(rvz_file, unzipped_folder)
            logging.info(f"Converted {rvz_file} to {iso_file}")

            # Step 4: Extract Game ID from the .iso file
            game_id = extract_game_id(iso_file)
            if not game_id:
                raise Exception(f"Failed to extract Game ID from {iso_file}.")
            
            # Step 5: Find the region and game name using the game ID in the parsed wiitdb
            game_info = find_game_info(game_id, wiitdb)
            region = game_info['region']
            game_name = game_info['game_name']
            logging.info(f"Detected game region: {region}, game name: {game_name}")

            # Step 6: Convert .iso to .wbfs
            logging.info(f"Converting {iso_file} to .wbfs")
            wbfs_file = convert_iso_to_wbfs(iso_file, unzipped_folder)
            logging.info(f"Converted {iso_file} to {wbfs_file}")

            # Log success and store the game for region checking
            log_process(zip_file, unzipped_folder, rvz_file, iso_file, wbfs_file, region, "Success")
            archive_games[game_id] = {'region': region, 'game_name': game_name, 'file_path': rvz_file}

        except Exception as e:
            # Log the failure for this zip file
            log_process(zip_file, None, None, None, None, None, "Failed", str(e))

    # After processing all files, check for games in multiple regions
    duplicate_games = find_duplicate_games_in_diff_regions(archive_games)
    if duplicate_games:
        print("Games found in multiple regions:")
        for game_identifier, games in duplicate_games.items():
            print(f"Game {game_identifier}:")
            for game_id, region, game_name, file_path in games:
                print(f"  - {game_id} ({region}, {game_name}, {file_path})")
    else:
        print("No games found in multiple regions.")


if __name__ == "__main__":
    process_files()
