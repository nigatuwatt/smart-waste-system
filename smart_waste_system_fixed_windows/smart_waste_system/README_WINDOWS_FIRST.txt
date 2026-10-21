SMART WASTE COLLECTION — STARTING ON WINDOWS

IMPORTANT: app.py must be run through Streamlit, not by double-clicking app.py
or using `python app.py`.

EASY METHOD
1. Extract the ZIP file first.
2. Open the smart_waste_system folder (the one containing app.py and requirements.txt).
3. Double-click INSTALL_AND_RUN.bat.
4. The first run creates .venv and installs the packages. This needs internet access.
5. The dashboard should open in your browser at an address such as http://localhost:8501.
6. Later, double-click RUN_APP.bat to start it again.

COMMAND PROMPT METHOD
Open Command Prompt and run:
  cd /d "C:\Users\Hybrid\Documents\Ai Hill Climbing project\smart_waste_system_fixed\smart_waste_system"
  python -m venv .venv
  .venv\Scripts\python.exe -m pip install --upgrade pip
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  .venv\Scripts\python.exe -m pytest -q
  .venv\Scripts\python.exe -m streamlit run app.py

If your extracted directory name differs, adjust the cd path. A requirements.txt error
usually means the terminal is not inside the folder that contains requirements.txt.
A 'No module named plotly' error means the dependencies have not been installed into
the same Python environment used to run the app.

The app's OpenStreetMap/OSRM mode requires internet access. Select Simulated demo data
for the offline demonstration. OSM results for broad area names must be checked and are
not guaranteed to identify an actual waste-bin entrance.
