import subprocess
import time
import re

# Define the bash script you want to run
bash_script = "./run_cluster.sh"

# Define the timeout in seconds
timeout_seconds = 20

# Start the process
process = subprocess.Popen(
    bash_script,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True
)

# Capture output in real time
output_lines = []
start_time = time.time()

ru_pattern = re.compile("RU from (\\d+)")
ru_counter = 0
ru_dict = {}

try:
    # Continuously check process output until the timeout
    while True:
        # Check if process has output to read
        if process.stdout is not None:
            line = process.stdout.readline()

            if line and "exited with code" not in line:
                match = ru_pattern.search(line)
                if match:
                    ru_counter += 1
                    print(match.group(1))
                    value = ru_dict.get(match.group(1), 0) + 1
                    ru_dict[match.group(1)] = value
                    
                output_lines.append(line)
                print(line.strip())  # Optional: print each line as it comes in

        # Check if process has exceeded the timeout
        if time.time() - start_time > timeout_seconds:
            print("Terminating process.")
            raise subprocess.TimeoutExpired(bash_script, timeout_seconds)
        
        # If process completes on its own, break
        if process.poll() is not None:
            break

except (subprocess.TimeoutExpired, KeyboardInterrupt) as e:
    print(e)
    print(f"\nThe script was killed after {timeout_seconds} seconds due to timeout.")
    process.terminate()  # Stop the process if timeout is reached
    print(ru_counter)
    print(ru_dict)

# Process the output: count the number of lines
line_count = len(output_lines)
print(f"\nThe script output contains {line_count} lines (partial output if killed due to timeout).")
