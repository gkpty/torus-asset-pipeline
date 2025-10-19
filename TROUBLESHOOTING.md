# Troubleshooting Guide

## Common Issues and Solutions

### 1. Script Gets Stuck After "Yes" to Continue

**Symptoms:**
- You type "yes" to continue downloading
- The script appears to hang with no output
- No progress bars or further messages appear

**Possible Causes & Solutions:**

#### A. Authentication Issues
The most common cause is that the Google Drive authentication is hanging.

**Solution:**
1. Run the authentication test:
   ```bash
   python test_auth.py
   ```

2. If authentication fails, check:
   - Your `credentials.json` file exists and is valid
   - You have internet connection
   - Your Google account has access to the Google Drive API

#### B. Browser Authentication Hanging
The authentication process opens a browser window that might not be visible or might be blocked.

**Solution:**
1. Look for a browser window that opened automatically
2. Complete the Google authentication in the browser
3. If no browser opened, try running with debug mode:
   ```bash
   python cli.py download --debug
   ```

#### C. Network/Firewall Issues
Your network might be blocking the authentication process.

**Solution:**
1. Check if you're behind a corporate firewall
2. Try running from a different network
3. Check if port 8080 is available (used for authentication)

### 2. Debug Mode

Use debug mode to see detailed logging:

```bash
python cli.py download --debug
```

This will show:
- Authentication progress
- Folder access attempts
- Detailed error messages
- Step-by-step progress

### 3. Test Authentication Only

Run the authentication test script:

```bash
python test_auth.py
```

This will:
- Test your credentials file
- Test Google Drive authentication
- Test API access
- Test folder access (if you provide a folder ID)

### 4. Common Error Messages

#### "Credentials file not found"
- **Solution:** Ensure `credentials.json` exists in the project root
- **Check:** Run `ls -la credentials.json` to verify the file exists

#### "Authentication failed"
- **Solution:** Check your credentials file format
- **Check:** Ensure the file is valid JSON and contains proper Google API credentials

#### "No suppliers found in the specified folder"
- **Solution:** Verify the folder ID is correct
- **Check:** Ensure the folder contains subfolders (suppliers)
- **Check:** Ensure you have access to the folder

#### "Error accessing folder"
- **Solution:** Check if the folder ID is correct
- **Check:** Ensure you have read access to the folder
- **Check:** Ensure the folder exists and is accessible

### 5. Step-by-Step Debugging

1. **Test basic authentication:**
   ```bash
   python test_auth.py
   ```

2. **Test with debug mode:**
   ```bash
   python cli.py download --debug
   ```

3. **Test with a specific folder:**
   ```bash
   python cli.py download YOUR_FOLDER_ID products --debug
   ```

4. **Check your configuration:**
   ```bash
   python cli.py config
   ```

### 6. Manual Authentication Test

If the automated authentication is failing, you can test it manually:

```python
from modules.download import GoogleDriveDownloader

# Create downloader instance
downloader = GoogleDriveDownloader("credentials.json")

# Test authentication
try:
    service = downloader.authenticate()
    print("Authentication successful!")
except Exception as e:
    print(f"Authentication failed: {e}")
```

### 7. Browser Issues

If the browser doesn't open automatically:

1. **Check if a browser window opened in the background**
2. **Look for a localhost URL in your terminal** (usually `http://localhost:8080`)
3. **Manually open the URL in your browser**
4. **Complete the Google authentication process**

### 8. Port Issues

If you get port-related errors:

1. **Check if port 8080 is in use:**
   ```bash
   lsof -i :8080
   ```

2. **Kill any processes using port 8080:**
   ```bash
   kill -9 $(lsof -t -i:8080)
   ```

3. **Try running the script again**

### 9. Still Having Issues?

If you're still experiencing problems:

1. **Check the logs:** Run with `--debug` and `--verbose` flags
2. **Verify your setup:** Ensure all dependencies are installed
3. **Test with a simple folder:** Try with a folder you know you have access to
4. **Check Google Drive permissions:** Ensure your account has the necessary permissions

### 10. Getting Help

When reporting issues, please include:

1. **Error messages** (full output)
2. **Debug output** (run with `--debug`)
3. **Your operating system**
4. **Python version** (`python --version`)
5. **Whether authentication test passes** (`python test_auth.py`)

## Quick Fixes

### Reset Authentication
If authentication is stuck, try:
1. Close any browser windows
2. Kill any Python processes
3. Run the script again

### Check Credentials
```bash
# Check if credentials file exists
ls -la credentials.json

# Check if it's valid JSON
python -c "import json; print(json.load(open('credentials.json')))"
```

### Test Network Access
```bash
# Test if you can reach Google APIs
curl -I https://www.googleapis.com
```
