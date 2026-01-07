# 🔧 .env Configuration Guide

## ✅ Correct Format

```dotenv
# No quotes around values!
GEMINI_API_KEY=AIzaSyDkF5qLDOEHZG-S4ChyrgHyq9Rvy09pyDU

DB_HOST=aws-1-ap-south-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.gtlojusiykbjvuzsrgdi
DB_PASSWORD=6yFHqCMg9ATcCRZt
```

## ❌ WRONG Format

```dotenv
# Don't use quotes - they become part of the value!
DB_HOST="aws-1-ap-south-1.pooler.supabase.com"  # ❌ WRONG
DB_PASSWORD="your_password"  # ❌ WRONG
```

## 🐛 Why Quotes Fail

python-dotenv treats quotes as **literal characters**:

```python
# With quotes in .env:
DB_PASSWORD="abc123"

# Python reads:
os.getenv('DB_PASSWORD')  # Returns: "abc123" (WITH quotes!)

# PostgreSQL tries to auth with:
password = '"abc123"'  # ❌ Fails! Quotes aren't part of password
```

## ✅ Without Quotes (Correct)

```python
# Without quotes in .env:
DB_PASSWORD=abc123

# Python reads:
os.getenv('DB_PASSWORD')  # Returns: abc123 (NO quotes)

# PostgreSQL auth succeeds:
password = 'abc123'  # ✅ Correct password
```

## 📝 Rules for .env Files

1. **No quotes around values** (unless quotes are part of the actual value)
2. **No spaces around `=`**: `KEY=value` ✅ not `KEY = value` ❌
3. **Use ASCII comments only**: `# This works` ✅ not `# Tiếng Việt` ❌
4. **One variable per line**
5. **Empty lines are OK**

## 🔍 Debugging

Test your .env loads correctly:

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Password:', os.getenv('DB_PASSWORD'))"
```

Should print password WITHOUT quotes.

## 🎯 Summary

| Issue | Cause | Fix |
|-------|-------|-----|
| Auth fails | Quotes in .env values | Remove all quotes |
| Encoding error | UTF-8 comments | Use ASCII comments |
| NULL values | Spaces around `=` | No spaces: `KEY=value` |

**Golden Rule:** `.env` values should be raw text without decorators!
