import json
import csv


def json_to_csv(json_file, csv_file):
    # Open the JSON file and load data
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return
    
    if not data:
        print("JSON file is empty or invalid. Exiting...")
        return

    # Assuming the data is a list of dictionaries
    # Extracting data to write to the CSV file
    try:
        with open(csv_file, "w", newline="") as file:
             writer = csv.writer(file)   
             # Writing the header
             header = data[0].keys()
             writer.writerow(header)
             
             # Writing data rows
             for entry in data:
                writer.writerow(entry.values())
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        return

if __name__ == "__main__":
    json_to_csv("unused_iam_roles.json", "converted.csv")


# Example usage
# json_to_csv("path_to_your_json_file.json", "desired_output_file_name.csv")
