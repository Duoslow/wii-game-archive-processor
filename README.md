# Wii Game Archive Processor

This Python project processes a folder of `.zip` files containing game files, converts them to various formats, extracts game metadata, logs the process into an SQLite database, and detects duplicate games in different regions. It relies on external tools for file conversion and supports downloading required utilities if not already available.

## Features

- **File Extraction**: Unzips `.zip` archives to extract `.rvz` game files.
- **Format Conversion**: Converts `.rvz` files to `.iso` using `DolphinTool` and `.iso` to `.wbfs` using `wit`.
- **Game Metadata Extraction**: Extracts game ID and region data from `.iso` files.
- **Logging**: Logs process details and errors into a SQLite database.
- **Duplicate Detection**: Detects games available in multiple regions using a lookup from `wiitdb.txt`.

## Prerequisites

### Python Packages

- Install the required Python packages by running:
  ```bash
  pip install -r requirements.txt
  ```
  *Required packages: `requests`, `py7zr`, `sqlite3`, `shutil`, `logging`, `zipfile`, `subprocess`, `struct`, `collections`.*

### External Tools

- **DolphinTool.exe**: Used to convert `.rvz` files to `.iso` format.
- **wit.exe**: Used to convert `.iso` files to `.wbfs` format.
- **wiitdb.txt**: Database used to map game IDs to game names and regions.

If the required tools are not found locally, the project will attempt to download them automatically.

## Setup Instructions

1. Clone this repository:
    ```bash
    git clone https://github.com/Duoslow/wii-game-archive-processor.git
    ```
2. Navigate to the project directory:
    ```bash
    cd wii-game-archive-processor
    ```
3. Ensure that the archive folder `games` contains your `.zip` files.

4. Run the program:
    ```bash
    python main.py
    ```

## How It Works

1. The script sets up logging to track all operations in a log file `file_processing.log`.
2. It downloads the necessary external tools (`DolphinTool.exe`, `wit.exe`, and `wiitdb.txt`) if they are not found.
3. It processes all `.zip` files in the `games` folder by:
   - Extracting `.rvz` files.
   - Converting `.rvz` to `.iso` using DolphinTool.
   - Extracting game ID from the `.iso`.
   - Using the game ID to determine the game region and name from `wiitdb.txt`.
   - Converting `.iso` to `.wbfs` using `wit`.
4. Logs all processes in a SQLite database (`file_processing_log.sqlite`).
5. Detects games available in multiple regions and logs them into the database.

## Folder Structure

```plaintext
wii-game-archive-processor/
│
├── games/                  # Folder containing .zip files of game archives
│   ├── game1.zip
│   ├── game2.zip
│   └── ...
│
├── DolphinTool.exe             # Tool for converting .rvz to .iso
├── wit.exe                     # Tool for converting .iso to .wbfs
├── wiitdb.txt                  # Database for game ID lookup (game name and region)
├── file_processing_log.sqlite  # SQLite database for logging
├── file_processing.log         # Log file for all operations
├── main.py                     # Main script for processing game archives
├── requirements.txt            # Required Python packages
└── README.md                   # Project documentation
```

## Database Structure

- **`process_log`**: Logs each processed game, including any errors.
- **`duplicate_games`**: Logs any games found in multiple regions.

## Error Handling

- The script handles and logs errors during file extraction, conversion, or metadata parsing.
- The status and error message (if any) are recorded in the SQLite database.

## Dependencies

- **Python 3.6+**
- **External Tools**:
  - [DolphinTool](https://dolphin-emu.org)
  - [Wiimm's ISO Tools (wit)](https://wit.wiimm.de)
  
## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

This project was developed to help streamline the processing and conversion of game archives for Wii platforms.