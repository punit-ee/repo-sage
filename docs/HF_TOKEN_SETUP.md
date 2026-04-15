# HuggingFace Token Setup Guide

## Why Do I See This Warning?

When you use the search functionality, you might see:
```
Warning: You are sending unauthenticated requests to the HF Hub.
Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```

This warning appears when downloading sentence-transformer models from HuggingFace Hub without authentication.

## Do I Need to Fix It?

**No, it's optional!** The system works fine without the token. However, setting it up gives you:

✅ **Faster downloads** - Higher priority in download queues
✅ **Higher rate limits** - More requests allowed
✅ **No warnings** - Cleaner output

## How to Set Up HF_TOKEN

### Step 1: Get Your Token

1. Go to [HuggingFace](https://huggingface.co)
2. Sign up for a free account (if you don't have one)
3. Go to [Settings → Access Tokens](https://huggingface.co/settings/tokens)
4. Click "New token"
5. Give it a name (e.g., "repo-sage")
6. Select "Read" permission
7. Click "Generate token"
8. Copy the token (it looks like: `hf_xxxxxxxxxxxxx`)

### Step 2: Add to .env File

Open your `.env` file and add:

```bash
HF_TOKEN=hf_your_actual_token_here
```

Your complete `.env` file should look like:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-key

# HuggingFace Token (Optional but recommended)
HF_TOKEN=hf_your_huggingface_token
```

### Step 3: Restart Your Application

The token is loaded when your Python script starts, so restart to pick up the change.

## Verify Setup

Run the setup check script:

```bash
python setup_check.py
```

You should see:
```
✅ HF_TOKEN: SET
```

## Alternative: Set Environment Variable

Instead of using `.env`, you can set it as an environment variable:

### Linux/Mac:
```bash
export HF_TOKEN=hf_your_token_here
python your_script.py
```

### Windows (PowerShell):
```powershell
$env:HF_TOKEN="hf_your_token_here"
python your_script.py
```

### Windows (CMD):
```cmd
set HF_TOKEN=hf_your_token_here
python your_script.py
```

## Troubleshooting

### Still seeing the warning?

1. **Check your .env file location** - It should be in the project root
2. **Verify the token format** - Should start with `hf_`
3. **Restart your script** - Changes require restart
4. **Check for typos** - Variable name is `HF_TOKEN` (not `HF_API_KEY`)

### Token not working?

1. Make sure the token has "Read" permissions
2. Token should not be expired
3. Check if there are any spaces in the `.env` file line

## FAQ

**Q: Is my token secure in .env file?**
A: Yes, if you don't commit it to git. Make sure `.env` is in your `.gitignore`.

**Q: Can I use the same token for multiple projects?**
A: Yes! One HF token works for all your projects.

**Q: What if I don't want to set it up?**
A: That's fine! Just ignore the warning. Everything works without it.

**Q: Will it make my code faster?**
A: Only the first time downloading models. After that, models are cached locally.

## Summary

```bash
# Quick Setup
1. Get token: https://huggingface.co/settings/tokens
2. Add to .env: HF_TOKEN=hf_xxxxx
3. Restart your script
4. ✅ Done!
```

**Note**: This is completely optional. Your code works fine without it!
