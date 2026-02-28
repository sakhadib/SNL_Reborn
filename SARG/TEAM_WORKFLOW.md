# Team Training Workflow - Quick Reference

## ✅ YES - This is EXACTLY the workflow!

### You (Person 1):
```bash
# Start training
python3 train_rl.py --phase 1 --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42

# When tired, press Ctrl+C
# System saves:
#   ✓ training_state.json (auto-saved)
#   ✓ rl_v1_interrupted.zip (emergency checkpoint)

# Commit tracking files to GitHub
git add data/rl_checkpoints/training_state.json
git add data/rl_evaluation/
git add data/rl_logs/
git commit -m "Training: 325k episodes, Phase 1, WR: 72.3%"
git push

# Upload model to Google Drive/Dropbox
# Share link with team: "Models at: https://drive.google.com/..."
```

### Friend (Person 2):
```bash
# Pull latest tracking files
git pull

# Download models from your shared link
# Put in: data/rl_checkpoints/

# Resume training (--resume automatically loads training_state.json)
python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42

# Train for a while, then Ctrl+C

# Commit and share
git add data/rl_checkpoints/training_state.json data/rl_evaluation/ data/rl_logs/
git commit -m "Training: 550k episodes, Phase 1, WR: 76.8%"
git push
# Upload new models to cloud, share link
```

### Teammate (Person 3):
```bash
# Same process
git pull
# Download models from Person 2's link
python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
# ... repeat cycle
```

---

## 🔄 The Cycle

1. **Run:** `python3 train_rl.py --resume ...` (or `--phase 1` for first time)
2. **Stop:** Press `Ctrl+C` when done
3. **Commit:** `git add` tracking files, `git commit`, `git push`
4. **Share:** Upload `.zip` models to cloud storage, share link with team
5. **Next person:** `git pull`, download models, go to step 1

---

## 📁 What Goes Where

### GitHub (Small Files):
```
data/rl_checkpoints/training_state.json   ← Tracks progress
data/rl_evaluation/*.json                 ← Evaluation results
data/rl_logs/*.log                        ← Training logs
```

### Cloud Storage (Large Files):
```
data/rl_checkpoints/rl_v1_latest.zip      ← Most recent model
data/rl_checkpoints/rl_v1_best.zip        ← Best performing model
data/rl_checkpoints/rl_v1_interrupted.zip ← Emergency save
data/rl_checkpoints/rl_v1_phaseN_complete.zip ← Phase completions
```

---

## 🚨 Important Rules

### ✅ DO:
- Always use `--resume` when continuing training
- Always `git push` tracking files after stopping
- Always share model `.zip` files via cloud storage
- Coordinate in team chat who's training when

### ❌ DON'T:
- Don't train simultaneously (will cause conflicts)
- Don't commit `.zip` files to GitHub (they're huge and in .gitignore)
- Don't delete `training_state.json` (it's the coordination hub)
- Don't skip the cloud storage step (teammates need those models!)

---

## 🔍 Verification Commands

```bash
# Check current training state
cat data/rl_checkpoints/training_state.json

# See what models you have locally
ls -lh data/rl_checkpoints/*.zip

# Check git status (should only see tracking files)
git status

# See recent evaluations
ls -lt data/rl_evaluation/ | head
```

---

## 💡 Pro Tips

### For Long Sessions:
```bash
# Run with nohup so it continues if SSH disconnects
nohup python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42 > training.log 2>&1 &

# Check progress
tail -f training.log
```

### Quick Status Check:
```bash
# See how many episodes trained
grep "total_episodes" data/rl_checkpoints/training_state.json

# See current win rate
grep "recent_win_rate" data/rl_checkpoints/training_state.json
```

### If Teammate Forgot to Upload Models:
Ask them to run:
```bash
ls data/rl_checkpoints/*.zip
# They should upload all these to cloud storage
```

---

## 🎯 Expected Timeline

**Total:** ~4-9M episodes over 2-4 days

**Typical shifts:**
- Person 1: 8am-2pm → 300k-500k episodes → Ctrl+C, commit, share
- Person 2: 3pm-9pm → 300k-500k episodes → Ctrl+C, commit, share  
- Person 3: 10pm-6am → 300k-500k episodes → Ctrl+C, commit, share
- Repeat until Phase 4 completes

**Checkpoints every 25k episodes = every ~1-2 hours**

---

## ✅ You're Ready!

**Your exact command:**
```bash
python3 train_rl.py --phase 1 --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
```

**When Ctrl+C:**
1. Training state auto-saved ✓
2. Emergency checkpoint saved ✓
3. Git commit tracking files ✓
4. Upload models to cloud ✓
5. Share link with team ✓

**Teammates continue:**
```bash
python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
```

**That's it! Super simple cycle. 🚀**
