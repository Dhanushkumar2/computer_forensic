# Step-by-Step Data Extraction and Display Guide

This guide will help you extract data from sample disk images and display them on the website.

## Prerequisites

1. MongoDB must be running
2. Sample disk images in `forensic_ir_app/data/samples/`
3. Python virtual environment activated

---

## Step 1: Check MongoDB Status

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# If not running, start it:
sudo systemctl start mongod
```

---

## Step 2: Verify Sample Disk Images

```bash
# List available disk images
ls -lh forensic_ir_app/data/samples/
```

You should see files like:
- `fdrive image.E01`
- `nps-2008-jean.E01`
- `nps-2008-jean.E02`

---

## Step 3: Extract Data from Disk Images

### Option A: Extract ALL sample images automatically

```bash
cd forensic_ir_app
python3 extract_samples.py
```

This will:
- Find all disk images in `data/samples/`
- Extract artifacts from each image
- Store everything in MongoDB
- Save backup JSON files in `data/extracted/`

### Option B: Extract a SPECIFIC disk image

```bash
cd forensic_ir_app
python3 extract_samples.py "data/samples/fdrive image.E01" "CASE_FDRIVE"
```

---

## Step 4: Verify Data in MongoDB

```bash
# Connect to MongoDB
mongosh

# Switch to forensic database
use forensic_ir_db

# Check collections
show collections

# Count documents in each collection
db.browser_artifacts.countDocuments()
db.usb_devices.countDocuments()
db.user_activity.countDocuments()
db.timeline_events.countDocuments()

# View a sample browser artifact
db.browser_artifacts.findOne()

# Exit MongoDB shell
exit
```

---

## Step 5: Start the Application

### Terminal 1: Start Backend

```bash
cd forensic_ir_app/backend
source ../../venv/bin/activate
python manage.py runserver 8000
```

Wait for: `Starting development server at http://127.0.0.1:8000/`

### Terminal 2: Start Frontend

```bash
cd forensic_ir_app/frontend
npm start
```

Wait for: `Compiled successfully!` and browser opens at `http://localhost:3000`

---

## Step 6: View Data on Website

1. **Open Browser**: Go to `http://localhost:3000`

2. **Select a Case**: 
   - Click on "Cases" in the sidebar
   - You should see the extracted case(s)
   - Click on a case to view details

3. **View Artifacts**:
   - Click "Artifacts" in the sidebar
   - Browse different artifact types:
     - Browser History
     - USB Devices
     - User Activity
     - Deleted Files
     - Event Logs

4. **View Timeline**:
   - Click "Timeline" in the sidebar
   - See chronological events from all artifacts

5. **View Dashboard**:
   - Click "Dashboard" in the sidebar
   - See statistics and charts

---

## Troubleshooting

### Problem: "No module named 'pyewf'"

```bash
# Install forensic libraries
sudo apt-get install libtsk-dev libewf-dev
pip install pytsk3 pyewf
```

### Problem: "Connection refused" to MongoDB

```bash
# Start MongoDB
sudo systemctl start mongod

# Check status
sudo systemctl status mongod
```

### Problem: "No disk images found"

```bash
# Check if images exist
ls -lh forensic_ir_app/data/samples/

# Make sure files have .E01, .dd, or .raw extensions
```

### Problem: Backend won't start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
cd forensic_ir_app/backend
pip install -r requirements.txt

# Run migrations
python manage.py migrate
```

### Problem: Frontend won't start

```bash
cd forensic_ir_app/frontend

# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Start again
npm start
```

---

## Quick Commands Reference

```bash
# Extract all samples
cd forensic_ir_app && python3 extract_samples.py

# Start backend
cd forensic_ir_app/backend && source ../../venv/bin/activate && python manage.py runserver

# Start frontend
cd forensic_ir_app/frontend && npm start

# Check MongoDB
mongosh forensic_ir_db --eval "db.browser_artifacts.countDocuments()"

# View extraction logs
tail -f forensic_ir_app/backend/logs/*.log
```

---

## What Happens During Extraction?

1. **Opens disk image** using pyewf and pytsk3
2. **Finds NTFS partition** and mounts filesystem
3. **Discovers user profiles** (e.g., /Users/John)
4. **Extracts artifacts**:
   - Browser history, cookies, downloads (Firefox, Chrome, IE)
   - Registry data (USB devices, installed programs, run keys)
   - Recycle bin (deleted files)
   - Event logs (system events)
   - Filesystem (prefetch, link files, jump lists)
5. **Stores in MongoDB** with proper indexing
6. **Creates timeline** from all timestamped events
7. **Saves JSON backup** for reference

---

## Expected Output

After successful extraction, you should see:

```
Processing: data/samples/fdrive image.E01
Case ID: CASE_FDRIVE

Starting extraction...
Extracting browser artifacts...
Extracting registry artifacts...
Extracting recycle bin artifacts...
Extracting event log artifacts...
Extracting filesystem artifacts...

=== EXTRACTION SUMMARY ===
  Total Browser History: 1247
  Total Browser Cookies: 856
  Total USB Devices: 12
  Total Userassist Entries: 2890
  Total Installed Programs: 145
  Total Deleted Files: 234
  Total Event Log Entries: 5678

📦 Storing artifacts in MongoDB...
  ✓ Browser artifacts: 2103
  ✓ USB devices: 12
  ✓ User activity: 2890
  ✓ Installed programs: 145
  ✓ Registry artifacts: 45
  ✓ Event logs: 5678
  ✓ Filesystem artifacts: 567
  ✓ Recycle bin artifacts: 234
  ✓ Timeline events: 11674

✅ Successfully stored all artifacts in MongoDB!
📄 Backup JSON saved to: data/extracted/CASE_FDRIVE_artifacts.json
```

---

## Next Steps

After extraction and viewing data:

1. **Run Anomaly Detection**: Click "AI Anomaly Detection" in sidebar
2. **Generate Reports**: Click "Reports" to create investigation reports
3. **Search Artifacts**: Use search bar to find specific data
4. **Export Data**: Download artifacts as CSV or JSON

---

## Need Help?

- Check logs: `forensic_ir_app/backend/logs/`
- View JSON backups: `forensic_ir_app/data/extracted/`
- Read documentation: `forensic_ir_app/QUICK_START.txt`
