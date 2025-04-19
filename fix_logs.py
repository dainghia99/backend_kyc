import os
import shutil
import time

def fix_logs():
    """
    Fix log file permissions and clean up any locked files
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    
    print(f"Checking log directory: {log_dir}")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        print("Creating logs directory...")
        os.makedirs(log_dir)
        print("✅ Logs directory created")
        return
    
    # Check if app.log exists and is locked
    log_file = os.path.join(log_dir, 'app.log')
    if os.path.exists(log_file):
        try:
            # Try to open the file in write mode to check if it's locked
            with open(log_file, 'a') as f:
                f.write("")
            print("✅ Log file is accessible")
        except (IOError, PermissionError) as e:
            print(f"❌ Log file is locked: {e}")
            print("Attempting to fix...")
            
            # Create a backup of the logs directory
            backup_dir = f"{log_dir}_backup_{int(time.time())}"
            try:
                shutil.copytree(log_dir, backup_dir)
                print(f"✅ Created backup at {backup_dir}")
            except Exception as e:
                print(f"⚠️ Could not create backup: {e}")
            
            # Try to remove the log file
            try:
                # Rename the file first (sometimes helps with locked files on Windows)
                temp_name = f"{log_file}.old"
                os.rename(log_file, temp_name)
                os.remove(temp_name)
                print("✅ Successfully removed locked log file")
            except Exception as e:
                print(f"⚠️ Could not remove log file: {e}")
                print("Please try manually deleting the log files or restarting your computer")
                return
    else:
        print("✅ Log file doesn't exist yet")
    
    # Check for rotated log files and try to clean them up
    for filename in os.listdir(log_dir):
        if filename.startswith('app.log.') or filename == 'app.log':
            file_path = os.path.join(log_dir, filename)
            try:
                with open(file_path, 'a') as f:
                    pass
            except (IOError, PermissionError):
                try:
                    os.remove(file_path)
                    print(f"✅ Removed locked rotated log file: {filename}")
                except Exception as e:
                    print(f"⚠️ Could not remove {filename}: {e}")
    
    print("\nLog directory should now be ready for use.")
    print("If you still encounter issues, please restart your computer to release any file locks.")

if __name__ == "__main__":
    fix_logs()
