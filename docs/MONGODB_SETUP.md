# MongoDB Atlas Free Tier Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create MongoDB Atlas Account
1. Go to https://www.mongodb.com/cloud/atlas/register
2. Sign up with email or Google account (free)
3. Verify your email

### Step 2: Create a Free Cluster (M0)
1. Click **"Build a Database"** or **"Create"**
2. Select **"M0 FREE"** tier
   - ✅ 512MB storage (sufficient for testing)
   - ✅ Shared RAM
   - ✅ No credit card required
3. Choose cloud provider: **AWS**, **Google Cloud**, or **Azure** (AWS recommended)
4. Select region closest to you
5. Cluster name: `investment-research` (or keep default)
6. Click **"Create Cluster"**

### Step 3: Create Database User
1. In **"Security > Database Access"**, click **"Add New Database User"**
2. Authentication Method: **Password**
3. Username: `investment_user` (or your choice)
4. Password: Click **"Autogenerate Secure Password"** and **save it**
   - Or create your own strong password
5. Database User Privileges: **Read and write to any database**
6. Click **"Add User"**

### Step 4: Whitelist Your IP Address
1. In **"Security > Network Access"**, click **"Add IP Address"**
2. Option 1 (Development): **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ Only for development! Not recommended for production
3. Option 2 (Secure): **"Add Current IP Address"**
   - More secure, but need to update if your IP changes
4. Click **"Confirm"**

### Step 5: Get Connection String
1. Go to **"Database"** → Click **"Connect"** on your cluster
2. Choose **"Connect your application"**
3. Driver: **Python**, Version: **3.12 or later**
4. Copy the connection string (looks like):
   ```
   mongodb+srv://investment_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password from Step 3

### Step 6: Add to .env File
1. Open your `.env` file (or create from `.env.template`)
2. Paste the connection string:
   ```bash
   MONGODB_URI=mongodb+srv://investment_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DB_NAME=investment_research
   ```
3. Make sure to replace `YOUR_PASSWORD` with the actual password!

## Verify Connection

Run this Python script to test the connection:

```python
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_connection():
    uri = "your_connection_string_here"
    client = AsyncIOMotorClient(uri)

    try:
        # Ping the database
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")

        # List databases
        db_list = await client.list_database_names()
        print(f"Available databases: {db_list}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        client.close()

asyncio.run(test_connection())
```

Or use the init script once Phase 2 is implemented:
```bash
python -m backend.scripts.init_db
```

## Free Tier Limits

✅ **Sufficient for this project**:
- 512MB storage (thousands of conversations)
- Shared vCPU and RAM
- No time limit (free forever!)
- No credit card required

❌ **Not included** (but we don't need them):
- Vector search (using ChromaDB instead)
- Dedicated resources
- Advanced monitoring

## Troubleshooting

### Connection Timeout
- Check Network Access settings (IP whitelist)
- Ensure password doesn't contain special characters that need URL encoding
  - If password has `@`, `#`, etc., URL-encode them:
    - `@` → `%40`
    - `#` → `%23`
    - Example: `p@ss#word` → `p%40ss%23word`

### Authentication Failed
- Double-check username and password
- Ensure user has "Read and write to any database" privileges

### Can't Find Connection String
- Go to Database → Click "Connect" → "Connect your application"
- Make sure driver is set to "Python"

## Next Steps

Once MongoDB is set up:
1. ✅ Connection string in `.env`
2. 🔜 Run Phase 2 to initialize database schema
3. 🔜 Set up ChromaDB (automatic, no configuration needed)

## Upgrade Path (Optional, Later)

When you're ready to deploy to production:
- **M2 tier**: $9/month (2GB storage, better performance)
- **M5 tier**: $25/month (5GB storage, dedicated resources)
- **M10+ tier**: $57/month (Vector search capability)
  - Only needed if you want to migrate from ChromaDB to MongoDB Vector Search
  - Not necessary for this project!
