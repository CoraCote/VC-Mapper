# VC-Mapper

## Project Setup & Usage

This project uses Python and several data science/geospatial libraries:
- streamlit
- pandas
- geopandas
- openpyxl
- shapely
- fiona
- folium
- pydeck

You can set up and run the project using either a Python virtual environment (venv) or a Conda/Mamba environment.

---

## 1. Using Python venv + pip

1. **Create a virtual environment (if not already created):**
   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment:**
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the app (example for Streamlit):**
   ```bash
   streamlit run your_app.py
   ```
   Replace `your_app.py` with your main script name.

---

## 2. Using Conda/Mamba

1. **Create the environment:**
   ```bash
   conda env create -f environment.yml
   # or, if using mamba
   mamba env create -f environment.yml
   ```
2. **Activate the environment:**
   ```bash
   conda activate vc-mapper
   ```
3. **Run the app (example for Streamlit):**
   ```bash
   streamlit run your_app.py
   ```
   Replace `your_app.py` with your main script name.

---

## Notes
- Make sure you have Python 3.10+ installed.
- If you add new dependencies, update `requirements.txt` and/or `environment.yml` accordingly.
- For geospatial libraries (like `geopandas`, `fiona`, `shapely`), Conda is often easier to resolve dependencies, especially on Windows. 