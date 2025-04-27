# Data Collector
1. Sign in to the platform
2. Ctrl + Shift + C to open developer console
3. Go to network tab, copy `Cookie` value in any request 
4. Replace the `COOKIE` value you copied in step 3 in `tm/api.py` file
5. Run script with `uv run main.py` for ongoing order or `uv run historical.py` for historical order past 2 months
