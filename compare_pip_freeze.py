import sys
from pathlib import Path

def read_requirements(file_path):
    """Reads a requirements or pip freeze output and returns a dictionary with package names as keys and versions as values."""
    if not Path(file_path).is_file():
        return {}
    with open(file_path, 'r',encoding='utf-8-sig') as file:
        packages = {}
        for line in file:
            if '==' in line:
                package, version = line.strip().split('==')
                packages[package] = version
        return packages

def compare_pip_freeze(current_file, previous_file, output_file):
    current = read_requirements(current_file)
    previous = read_requirements(previous_file)
    #print(current, previous)
    #print(current['numpy'], previous['numpy'])
    # Added, removed, and modified packages
    added = current.keys() - previous.keys()
    removed = previous.keys() - current.keys()
    modified = {pkg: (previous[pkg], current[pkg]) for pkg in current.keys() & previous.keys() if current[pkg] != previous[pkg]}

    # Write differences to output file
    with open(output_file, 'w') as file:
        if not added and not removed and not modified:
            file.write("No differences found.\n")
        else:
            if added:
                file.write("Added packages:\n")
                for pkg in added:
                    file.write(f"{pkg}=={current[pkg]}\n")
            if removed:
                file.write("\nRemoved packages:\n")
                for pkg in removed:
                    file.write(f"{pkg}\n")
            if modified:
                file.write("\nModified packages:\n")
                for pkg, (prev_version, curr_version) in modified.items():
                    file.write(f"{pkg}: {prev_version} -> {curr_version}\n")
    
    return added, removed, modified

if __name__ == "__main__":
    current_file = sys.argv[1]
    previous_file = sys.argv[2]
    output_file = sys.argv[3]

    added, removed, modified = compare_pip_freeze(current_file, previous_file, output_file)

    if added or removed or modified:
        print(f"Differences found. See {output_file} for details.")
    else:
        print("No differences found.")
