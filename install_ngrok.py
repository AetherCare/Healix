import urllib.request
import tarfile
import os

url = "https://equinox.io"
print("Downloading ngrok archive...")
urllib.request.urlretrieve(url, "ngrok.tar.gz")

print("Extracting files...")
with tarfile.open("ngrok.tar.gz", "r:gz") as tar:
    tar.extractall()

print("Moving binary to local paths...")
os.system("sudo mv ngrok /usr/local/bin/")

print("Cleaning up temporary workspace files...")
os.remove("ngrok.tar.gz")
print("Installation completed successfully!")
