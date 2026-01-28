"""
Convenience entrypoint so `python agent.py` works from the repo root.
This script launches the Streamlit application located in src/agent.py.
"""
import os
import sys
import subprocess

def main():
    # Use the current Python executable to run streamlit
    # This prevents path issues and ensures we use the same venv
    cmd = [sys.executable, "-m", "streamlit", "run", "src/agent.py"]
    
    # Pass along any additional arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    print(f"🚀 Launching Streamlit app: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running app: {e}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
