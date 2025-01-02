# level3-boolean-blind
 This code has been tested on desktop environments with a stable internet connection, as well as on servers, and works fine. 
  However, in Iran or on certain desktop setups, it may require running a proxy or VPN for proper functionality.

## Requirements

- Python 3.12.4 
- pip 24.3.1

## Dependencies

This code utilizes the following libraries. If the code does not work correctly, ensure these libraries are installed and properly imported:

- requests
- urllib3
- sys
- concurrent.futures (ThreadPoolExecutor, as_completed)
- time (sleep)

## How to Use

1. Open a terminal.
2. Navigate to the directory where the `level3-sqli-dumper.py` file exists.
3. Use the following command to run the script:
   ```bash

   python3 level3-sqli-dumper.py <URL>

   ```
   
### Example:

```bash

python3 level3-sqli-dumper.py https://y4yket215m.voorivex-lab.online/

```


