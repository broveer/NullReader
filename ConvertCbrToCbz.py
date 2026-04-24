import os
import subprocess
import shutil
import tempfile
import glob

SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
LIBRARY_DIR = "collections"

def convert_cbr_to_cbz():
    if not os.path.exists(SEVEN_ZIP):
        print(f"Error: 7-Zip not found at {SEVEN_ZIP}")
        print("Please install 7-Zip or update the path in this script.")
        return

    # Find all .cbr files recursively in the collections directory
    cbr_files = glob.glob(os.path.join(LIBRARY_DIR, "**", "*.cbr"), recursive=True)
    
    if not cbr_files:
        print("No .cbr files found. Everything is already .cbz!")
        return

    print(f"Found {len(cbr_files)} .cbr files. Starting conversion to .cbz...")

    for cbr_path in cbr_files:
        # Define paths
        dir_name = os.path.dirname(cbr_path)
        base_name = os.path.splitext(os.path.basename(cbr_path))[0]
        cbz_path = os.path.join(dir_name, base_name + ".cbz")

        print(f"\nConverting: {cbr_path}")
        print(f"To:         {cbz_path}")

        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Extract CBR using 7-Zip
            extract_cmd = [SEVEN_ZIP, "x", cbr_path, f"-o{temp_dir}", "-y"]
            try:
                subprocess.run(extract_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"Failed to extract {cbr_path}. Skipping.")
                continue

            # Step 2: Compress to CBZ (ZIP) format using 7-Zip or python's zipfile
            # Using python's shutil.make_archive for standard ZIP
            try:
                shutil.make_archive(os.path.splitext(cbz_path)[0], 'zip', temp_dir)
                # shutil.make_archive creates .zip, so we rename it to .cbz
                zip_path = os.path.splitext(cbz_path)[0] + ".zip"
                if os.path.exists(cbz_path):
                    os.remove(cbz_path) # remove exactly matching cbz if somehow it exists
                os.rename(zip_path, cbz_path)
            except Exception as e:
                print(f"Failed to create CBZ for {cbr_path}: {e}")
                continue

        # Step 3: Remove the original CBR
        try:
            os.remove(cbr_path)
            print(f"Successfully converted and deleted original CBR.")
        except Exception as e:
            print(f"Converted successfully, but failed to delete original CBR: {e}")

    print("\nConversion complete! Run UpdateLibrary.ps1 to update your config.json files.")

if __name__ == "__main__":
    convert_cbr_to_cbz()
