# Troubleshooting: Disk Images Not Showing in Website

## Problem
When creating a new case, the "Select Disk Image" dropdown is empty or shows "No disk images found".

## Quick Checklist

### 1. Verify Disk Images Exist
```bash
ls -lah forensic_ir_app/data/samples/
```

You should see files like:
- `fdrive image.E01`
- `nps-2008-jean.E01`
- `nps-2008-jean.E02`
- `image_jean`

### 2. Check Backend Server is Running
```bash
# Check if backend is running
curl http://localhost:8000/api/disk-images/

# Or check the process
ps aux | grep "manage.py runserver"
```

If not running, start it:
```bash
cd forensic_ir_app/backend
source ../../venv/bin/activate  # or source ../venv/bin/activate
python manage.py runserver 8000
```

### 3. Test the Disk Images Endpoint Directly
```bash
cd forensic_ir_app/backend
python test_disk_images_endpoint.py
```

This will show you:
- How many disk images were found
- Their details
- If the API endpoint is working

### 4. Check Frontend is Running
```bash
# Check if frontend is running
curl http://localhost:3000

# Or check the process
ps aux | grep "npm start"
```

If not running, start it:
```bash
cd forensic_ir_app/frontend
npm start
```

### 5. Check Browser Console
1. Open the website: http://localhost:3000
2. Open browser DevTools (F12)
3. Go to Console tab
4. Click "New Case" button
5. Look for error messages

Common errors:
- **Network Error**: Backend not running
- **CORS Error**: CORS not configured properly
- **404 Error**: API endpoint not found

### 6. Verify API URL Configuration
Check `forensic_ir_app/frontend/.env`:
```bash
cat forensic_ir_app/frontend/.env
```

Should contain:
```
REACT_APP_API_URL=http://localhost:8000/api
```

## Solutions

### Solution 1: Start Both Servers
```bash
# Terminal 1 - Backend
cd forensic_ir_app/backend
source ../../venv/bin/activate
python manage.py runserver 8000

# Terminal 2 - Frontend
cd forensic_ir_app/frontend
npm start
```

### Solution 2: Use the Startup Script
```bash
./forensic_ir_app/start_all.sh
```

### Solution 3: Test API Manually
```bash
# With backend running, test the endpoint
curl http://localhost:8000/api/disk-images/
```

Expected response:
```json
{
  "count": 4,
  "images": [
    {
      "filename": "fdrive image.E01",
      "path": "/path/to/forensic_ir_app/data/samples/fdrive image.E01",
      "size": 27262976,
      "size_formatted": "26.00 MB",
      "extension": ".E01",
      "modified": "2024-11-23T21:28:00"
    },
    ...
  ]
}
```

### Solution 4: Check CORS Settings
Edit `forensic_ir_app/backend/forensic_backend/settings.py`:

Make sure these are present:
```python
INSTALLED_APPS = [
    ...
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Should be near the top
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Or for development only:
CORS_ALLOW_ALL_ORIGINS = True
```

### Solution 5: Clear Browser Cache
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

## Verification Steps

After applying solutions:

1. **Backend Test**:
   ```bash
   curl http://localhost:8000/api/disk-images/
   ```
   Should return JSON with disk images

2. **Frontend Test**:
   - Open http://localhost:3000
   - Login
   - Click "New Case"
   - Check "Select Disk Image" dropdown
   - Should show 4 disk images

3. **Console Test**:
   - Open browser console (F12)
   - Should see logs like:
     ```
     Fetching disk images from: http://localhost:8000/api/disk-images/
     Disk images response: {count: 4, images: Array(4)}
     Number of images: 4
     ```

## Still Not Working?

Run the diagnostic script:
```bash
cd forensic_ir_app/backend
python test_disk_images_endpoint.py
```

Check the output and share any error messages.

## Common Issues

### Issue: "Network Error" in Console
**Cause**: Backend server not running
**Fix**: Start backend server

### Issue: "CORS Error" in Console
**Cause**: CORS not configured
**Fix**: Add CORS settings to Django settings.py

### Issue: Empty Array Returned
**Cause**: Disk images not in correct directory
**Fix**: Move disk images to `forensic_ir_app/data/samples/`

### Issue: "Connection Refused"
**Cause**: Backend not listening on port 8000
**Fix**: Check if another process is using port 8000
```bash
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```
