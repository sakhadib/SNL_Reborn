# Checkpoint Sharing for Team Collaboration

## Overview
This guide explains how to share training progress with teammates without Git LFS (avoiding GitHub's 1GB limit).

## What Gets Committed to Git

### ✅ Commit These (Small Files)
```bash
data/rl_checkpoints/training_state.json   # ~1KB - Training progress tracker
data/rl_evaluation/*.json                  # Evaluation reports
data/rl_logs/*.log                         # Training logs
```

### ❌ Never Commit These (Large Files - in .gitignore)
```bash
data/rl_checkpoints/*.zip                  # Model files (50-200MB each)
data/rl_checkpoints/snapshots/*.zip        # Snapshot models
data/games/*.bin                           # Game replays
```

## Workflow for Team Collaboration

### When YOU Finish Training
1. **Stop training** (Ctrl+C or let it complete a phase)
2. **Commit small files**:
   ```bash
   git add data/rl_checkpoints/training_state.json
   git add data/rl_evaluation/
   git add data/rl_logs/
   git commit -m "Training checkpoint at episode XXXXX, Phase N, WR: XX%"
   git push origin main
   ```

3. **Upload large model files to shared storage**:
   - Google Drive / Dropbox / OneDrive
   - Or use external transfer service (WeTransfer, etc.)
   - Share link in team chat/Discord/Slack
   
   Files to upload:
   ```bash
   data/rl_checkpoints/rl_v1_latest.zip      # Most recent model
   data/rl_checkpoints/rl_v1_best.zip        # Best performing model
   data/rl_checkpoints/rl_v1_phaseN_complete.zip  # Phase completions
   ```

### When TEAMMATE Wants to Continue

1. **Pull latest code and state**:
   ```bash
   git pull origin main
   ```

2. **Download model files**:
   - Get link from team chat
   - Download to `data/rl_checkpoints/`
   - Ensure filename matches what's in `training_state.json`

3. **Resume training**:
   ```bash
   python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
   ```

## Training State File (`training_state.json`)

This file tracks everything needed to resume:
```json
{
  "current_phase": 2,
  "total_episodes": 750000,
  "phase_episodes": 250000,
  "best_win_rate": 0.623,
  "recent_win_rate": 0.618,
  "timestamp": "2026-03-01T14:30:00",
  "checkpoint_file": "rl_v1_latest.zip"
}
```

## Best Practices

### 📊 Coordinate via Chat
- "I'm training Phase 2, will stop at 1M episodes"
- "Pushed state to GitHub, models in Drive link: [URL]"
- "Taking over training from episode 1.5M"

### 💾 Phase Completion Checkpoints
When a phase completes, the critical files are:
```bash
rl_v1_phase1_complete.zip  # Upload this to shared storage
rl_v1_phase2_complete.zip
rl_v1_phase3_complete.zip
rl_v1_phase4_complete.zip
```

### 🔄 Frequency
- Checkpoint every 25k-50k episodes (~1-2 hours)
- Push to GitHub every few hours
- Upload models to shared storage when switching who trains

## File Sizes (Approximate)

| File | Size | Share Via |
|------|------|-----------|
| `training_state.json` | ~1 KB | Git |
| `*.log` files | ~10-100 KB | Git |
| `*_evaluation/*.json` | ~5-20 KB | Git |
| `rl_v1_latest.zip` | ~50-200 MB | Cloud Storage |
| `rl_v1_best.zip` | ~50-200 MB | Cloud Storage |
| Phase checkpoints | ~50-200 MB each | Cloud Storage |

## Example Workflow Timeline

**Monday 9am - Alice:**
```bash
python3 train_rl.py --phase 1 --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
# Trains for 4 hours, reaches 500k episodes
# Ctrl+C to stop
git add data/rl_checkpoints/training_state.json data/rl_evaluation/ data/rl_logs/
git commit -m "Phase 1: 500k episodes, WR: 78.5%"
git push
# Uploads rl_v1_latest.zip to Google Drive, shares link
```

**Monday 2pm - Bob:**
```bash
git pull
# Downloads rl_v1_latest.zip from Alice's Drive link to data/rl_checkpoints/
python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
# Continues from 500k, trains to 1M episodes
# Phase 1 completes! File saved: rl_v1_phase1_complete.zip
# Ctrl+C
git add data/rl_checkpoints/training_state.json data/rl_evaluation/ data/rl_logs/
git commit -m "Phase 1 COMPLETE: 1M episodes, WR: 82%, advancing to Phase 2"
git push
# Uploads rl_v1_phase1_complete.zip + rl_v1_latest.zip to Drive
```

**Monday 6pm - Charlie:**
```bash
git pull
# Downloads models from Bob's link
python3 train_rl.py --resume --checkpoint-freq 25000 --eval-freq 50000 --log-freq 2500 --seed 42
# Starts Phase 2 training...
```

## Troubleshooting

### "Checkpoint file not found"
- Check `training_state.json` → `checkpoint_file` field
- Download that specific file from shared storage
- Put it in `data/rl_checkpoints/`

### "Phase mismatch"
- You're using `--phase X` but state says different phase
- Use `--resume` to continue from saved state
- Or use `--phase Y` to start fresh from that phase

### "Git says working tree is dirty"
- Normal! Model `.zip` files are ignored
- Only commit the small tracking files
- Never force-add `.zip` files to git

## Cloud Storage Recommendations

| Service | Free Tier | Best For |
|---------|-----------|----------|
| Google Drive | 15 GB | Small teams, easy sharing |
| Dropbox | 2 GB | Quick transfers |
| OneDrive | 5 GB | Microsoft teams |
| Mega.nz | 20 GB | Privacy-focused |
| Academic Cloud | Varies | University projects |

## Summary

✅ **DO:**
- Commit `training_state.json` and evaluation/log files to Git
- Upload model `.zip` files to cloud storage
- Coordinate who's training when
- Use `--resume` to continue training

❌ **DON'T:**
- Commit model `.zip` files to Git (they're huge!)
- Train simultaneously from same checkpoint (will conflict)
- Delete `training_state.json` (it's the coordination hub)

---

**Questions?** Check the state file first. It's the source of truth.
