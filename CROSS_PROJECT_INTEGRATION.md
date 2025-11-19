# Cross-Project Integration: Authentication vs Data Storage

## 🏗️ Architecture Overview

This implementation enables **authentication in one Google Cloud project** while **storing user data in another project**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Application                         │
│                  (React Native + Expo)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Project 1: reflect1-471514                      │
│                    🔐 AUTHENTICATION ONLY                       │
│                                                                 │
│  • Firebase Authentication                                     │
│  • User login/signup                                           │
│  • Email verification                                          │
│  • Returns: user.email                                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ user.email
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API Server                          │
│                   (reflect-git-backend)                        │
│                                                                 │
│  📧 Email Bridge: user_service.py                              │
│  • get_or_create_user(email)                                   │
│  • Converts email → Project 2 user_id                          │
└────────────────────────┬────────────────────────────────────────┘
                         │ internal_user_id
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Project 2: reflect-466215                      │
│                   💾 DATA STORAGE ONLY                         │
│                                                                 │
│  • Firestore Database (users, journals, conversations)         │
│  • PostgreSQL (embeddings, vector search)                      │
│  • Google Cloud AI (Gemini, embeddings)                        │
│  • All user data and analytics                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 How Cross-Project Bridge Works

### **Step 1: User Authentication (Project 1)**
```javascript
// Frontend authenticates with Project 1
const user = auth.currentUser; // Firebase Auth from reflect1-471514
const userEmail = user.email;  // "user@example.com"
```

### **Step 2: API Call with Email**
```javascript
// Frontend sends email as user_id
fetch('/store_journal', {
  method: 'POST',
  body: JSON.stringify({
    user_id: userEmail,        // Email from Project 1
    journal_text: "Today was great..."
  })
});
```

### **Step 3: Email-to-UserID Bridge (Backend)**
```python
# user_service.py - The Bridge Function
def get_or_create_user(email):
    # Check if user exists in Project 2 database
    users_ref = db.collection('users')  # Project 2 Firestore
    query = users_ref.where('email', '==', email).limit(1)
    
    if user_exists:
        return existing_user_data
    else:
        # Create new user in Project 2
        new_user = {
            'email': email,
            'created_at': datetime.now(),
            'journal_count': 0,
            'conversation_count': 0
        }
        doc_ref = users_ref.add(new_user)
        return new_user_data
```

### **Step 4: Data Storage with Internal ID (Project 2)**
```python
# journal_service.py - Updated to use bridge
def analyze_store_and_embed_journal(data):
    user_email = data.get("user_id")  # Email from Project 1
    
    # BRIDGE: Convert email to Project 2 internal ID
    user_data = get_or_create_user(user_email)
    internal_user_id = user_data['user_id']
    
    # Store journal under Project 2 internal user ID
    db.collection("users").document(internal_user_id)\
      .collection("journals").document(journal_id).set({
        "journal_text": journal_text,
        "user_email": user_email,  # Keep email for reference
        "created_at": datetime.utcnow()
    })
```

## 📊 Database Structure in Project 2

### **Firestore Collections:**
```
users/
├── {internal_user_id_1}/
│   ├── email: "user1@example.com"
│   ├── created_at: timestamp
│   ├── journal_count: 5
│   ├── conversation_count: 12
│   ├── journals/
│   │   ├── {journal_id_1}/
│   │   │   ├── journal_text: "..."
│   │   │   ├── summary: "..."
│   │   │   ├── user_email: "user1@example.com"
│   │   │   └── created_at: timestamp
│   │   └── {journal_id_2}/...
│   └── conversation_summary/
│       ├── {conversation_id_1}/
│       │   ├── summary_text: "..."
│       │   ├── user_email: "user1@example.com"
│       │   └── created_at: timestamp
│       └── {conversation_id_2}/...
└── {internal_user_id_2}/...
```

### **PostgreSQL Tables:**
```sql
-- Vector embeddings stored with email as user_id for consistency
journal_embeddings (
    user_id VARCHAR,        -- Email from Project 1
    journal_id VARCHAR,
    embedding VECTOR,
    created_at TIMESTAMP
);

conversation_embeddings (
    user_id VARCHAR,        -- Email from Project 1  
    summary_id VARCHAR,
    embedding VECTOR,
    created_at TIMESTAMP
);
```

## 🔗 Updated API Endpoints

### **Existing APIs (Modified for Cross-Project)**
```python
# All APIs now expect email as user_id parameter

POST /store_journal
Body: {"user_id": "email@example.com", "journal_text": "..."}

POST /therapist  
Body: {"user_id": "email@example.com", "query": "...", "top_k": 5}

GET /get_persona?user_id=email@example.com

GET /get_journals_summary?user_id=email@example.com&journal_ids=id1,id2

POST /search_journal
Body: {"user_id": "email@example.com", "query": "...", "top_k": 5}
```

### **New User Management APIs**
```python
# Get user profile from Project 2
GET /user/profile?email=user@example.com

# Update user preferences  
PUT /user/preferences
Body: {"email": "user@example.com", "preferences": {...}}

# Get user statistics
GET /user/stats?email=user@example.com
```

## 🚀 Testing the Integration

### **1. Start Backend Server**
```bash
cd reflect-git-backend
python main.py
```

### **2. Test Journal Storage**
```bash
curl -X POST http://localhost:5000/store_journal \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "journal_text": "Today I learned about cross-project integration!"
  }'
```

### **3. Test Chatbot**
```bash
curl -X POST http://localhost:5000/therapist \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com", 
    "query": "How can I manage stress better?",
    "top_k": 3
  }'
```

### **4. Test User Profile**
```bash
curl -X GET "http://localhost:5000/user/profile?email=test@example.com"
```

## ✅ Benefits of This Architecture

1. **🔐 Security Separation**: Authentication isolated from data storage
2. **📈 Scalability**: Each project can scale independently  
3. **💰 Cost Management**: Different billing for auth vs storage
4. **🛡️ Data Privacy**: Sensitive data separated from auth
5. **🔄 Flexibility**: Easy to switch auth providers without affecting data
6. **📊 Analytics**: Comprehensive user analytics in Project 2

## 🎯 Frontend Changes Required

**No changes needed!** Your existing frontend code will work as-is because:
- Firebase Auth still uses Project 1 (reflect1-471514)
- API calls still send `user_id` field with email
- Backend handles the cross-project bridge transparently

## 🔧 Configuration Files

### **Frontend: firebase.js (Project 1)**
```javascript
const firebaseConfig = {
  projectId: "reflect1-471514",         // ✅ Auth Project
  authDomain: "reflect1-471514.firebaseapp.com",
  // ... other config
};
```

### **Backend: config.py (Project 2)**
```python
PROJECT_ID = "reflect-466215"          # ✅ Data Storage Project
REGION = "us-central1"
```

This architecture gives you the best of both worlds: secure authentication management in Project 1 and powerful data analytics in Project 2! 🚀