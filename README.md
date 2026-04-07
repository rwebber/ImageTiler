# ImageTiler

**ImageTiler** is a simple graphical utility for creating large tiled mosaic images from a sequence of smaller image tiles. Built using **Python 3**, **PySide6 (Qt)**, and **OpenCV**, it's designed to handle large datasets and 64-bit systems efficiently.

---

## 📸 Features

- **Sequential Image Support**: Automatically detects and loads image sequences.
- **Customizable Mosaic Layout**: Set the number of columns to determine the width of the final mosaic.
- **Large Image Handling**: Built with 64-bit support to handle high-resolution output.
- **Real-time Feedback**: Simple UI indicators show if the selected range fits the column count perfectly.

---

## 🛠️ Requirements & Installation

### Prerequisites
- Python 3.x (64-bit recommended for large mosaics)
- Virtual Environment (recommended)

### Installation
1. Clone the repository or download the source files.
2. Install dependencies using pip:
   ```cmd
   pip install -r requirements.txt
   ```

---

## 🚀 Usage

### Running the Application
Launch the main application by running:
```cmd
python main.py
```

### How to Use
1. **Source Image**: Click the folder button to select the first image in your sequence.
2. **File Naming**: Ensure your images are named sequentially (e.g., `image_001.png`, `image_002.png`, or `file0001.jpg`).
3. **Range**: Set the start and end values for the image sequence. The app will calculate the total count.
4. **Columns**: Specify how many columns wide you want your final mosaic to be.
5. **Save Path**: Choose where to save the output and provide a name.
6. **Process**: Click the **Process** button to generate the mosaic.

---

## 🏗️ Development & GUI

### Modifying the GUI
The interface is designed in **Qt Designer** (`first.ui`). If you make changes to the `.ui` file, you must regenerate the Python GUI code:
```cmd
convertGui2py.bat
```
*Or manually:*
```cmd
pyside6-uic first.ui -o gui.py
```

---

## 📦 Building the Executable

You can package **ImageTiler** into a standalone Windows executable using the provided `build_exe.py` script.

### Basic Build
To create a standard folder-based build (recommended for stability):
```cmd
python build_exe.py --onedir
```

### Single EXE Build
To create a single, portable executable:
```cmd
python build_exe.py --onefile
```

### Build Options
- `--windowed`: Run without a console window (default).
- `--no-window`: Keep the console for debugging.
- `--icon <path>`: Specify a custom `.ico` file.
- `--clean`: Clean PyInstaller cache before building.

The output will be located in the `dist/` directory.

---

## 📄 License
Created by **DusX**.
