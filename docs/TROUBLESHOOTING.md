# Troubleshooting Guide

Common issues and how to resolve them.

## Installation Issues

### ModuleNotFoundError: No module named 'foldify'

**Problem:** Package not installed or installed in wrong environment.

**Solutions:**
```bash
# Install in editable mode
pip install -e "."

# Or install from PyPI (when published)
pip install foldify

# Verify installation
python -c "from foldify import __version__; print(__version__)"
```

### ImportError: No module named 'yaml'

**Problem:** Dependencies not installed.

**Solution:**
```bash
pip install -r requirements.txt
# Or
pip install pyyaml click
```

## Configuration Issues

### Profile not found

**Error:** `FileNotFoundError: Profile 'name' not found`

**Solutions:**
1. Check profile exists:
   ```bash
   foldify list
   ```

2. Verify profile location:
   ```bash
   ls ~/.config/foldify/profiles/
   ```

3. Create from template:
   ```bash
   foldify init --template school --profile school
   ```

### ValidationError: Profile must have at least one source

**Problem:** Profile is missing required `sources` section.

**Solution:**
```yaml
sources:
  - path: ~/Downloads  # Add this section
```

### ValidationError: Source 0: Path does not exist

**Problem:** Source directory doesn't exist.

**Solutions:**
1. Create the directory:
   ```bash
   mkdir -p ~/Downloads
   ```

2. Update profile to use existing directory:
   ```yaml
   sources:
     - path: ~/Desktop  # Change to existing path
   ```

### ValidationError: Multiple destinations point to the same path

**Problem:** Two destinations have identical paths.

**Solution:** Ensure each destination has a unique path:
```yaml
destinations:
  Math:
    path: ~/Documents/Math
  Physics:  # Different path
    path: ~/Documents/Physics
```

## Runtime Issues

### No files being moved (dry run mode)

**Symptom:** Preview shows files but nothing moves.

**Cause:** `dry_run: true` is set.

**Solutions:**
1. Run with `--dry-run` flag to explicitly control:
   ```bash
   foldify run --profile school --dry-run  # Preview
   foldify run --profile school           # Execute
   ```

2. Or edit profile:
   ```yaml
   options:
     dry_run: false
   ```

### Permission denied errors

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solutions:**
1. Check source directory permissions:
   ```bash
   ls -la ~/Downloads
   ```

2. Run with appropriate user (don't use sudo):
   ```bash
   # Ensure you own the files
   chown -R $USER:$USER ~/Downloads
   ```

3. Check destination is writable:
   ```bash
   touch ~/Documents/test_write && rm ~/Documents/test_write
   ```

### Files not matching any rules

**Symptom:** Files scanned but none matched.

**Debugging:**
1. Enable verbose mode:
   ```bash
   foldify run --profile school --verbose
   ```

2. Check include/exclude patterns:
   ```yaml
   sources:
     - path: ~/Downloads
       include_patterns: ["*"]  # Make sure files are included
       exclude_patterns: []       # Not excluded
   ```

3. Verify rules match file names:
   ```yaml
   rules:
     - type: filename_contains
       keywords: ["math"]  # Case-insensitive match
   ```

## AI Issues

### AI classification not working

**Symptom:** AI enabled but files not classified.

**Check:**
```bash
foldify ai status
```

**Solutions:**

1. **Ollama not installed:**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Model not pulled:**
   ```bash
   ollama pull qwen3:8b
   ```

3. **Ollama not running:**
   ```bash
   # Start Ollama
   ollama serve

   # Or as service
   sudo systemctl start ollama
   ```

4. **Model name incorrect:**
   ```yaml
   ai:
     model: qwen3:8b  # Check with: ollama list
   ```

### AI returns wrong categories

**Problem:** AI categorizes files incorrectly.

**Solutions:**

1. **Add more specific categories:**
   ```yaml
   ai:
     categories:
       - Algebra
       - Calculus
       - Physics_Mechanics
       - Physics_Optics
   ```

2. **Lower confidence threshold:**
   ```yaml
   ai:
     confidence_threshold: 0.5  # Try lower value
   ```

3. **Increase content length:**
   ```yaml
   ai:
     max_content_length: 5000  # Read more content
   ```

4. **Add filename rules first:**
   ```yaml
   rules:
     - type: filename_contains
       keywords: ["algebra"]
     # AI is fallback after rules
   ```

### Slow AI performance

**Problem:** AI classification takes too long.

**Solutions:**

1. **Use a smaller model:**
   ```bash
   ollama pull phi4:mini  # Faster
   ```

2. **Reduce content length:**
   ```yaml
   ai:
     max_content_length: 1000  # Analyze less text
   ```

3. **Enable caching:**
   ```yaml
   ai:
     cache_results: true  # Avoid re-processing
   ```

4. **Reduce workers:**
   ```yaml
   options:
     max_workers: 1  # Fewer concurrent requests
   ```

## File Type Issues

### PDF content not being read

**Problem:** `content_contains` rules don't match PDFs.

**Solutions:**

1. **Install pypdf:**
   ```bash
   pip install pypdf
   ```

2. **Check PDF is text-based:**
   ```bash
   # Scanned PDFs (images) won't work
   file document.pdf  # Should say "PDF document", not "PDF image"
   ```

### Word documents not being read

**Problem:** .docx files not processed.

**Solution:**
```bash
pip install python-docx
```

## Undo/Recovery

### Accidentally moved files

**Recovery:**

1. **Check for backups:**
   ```bash
   ls ~/.config/foldify/backups/
   ```

2. **Files backed up at destination:**
   ```bash
   ls ~/Documents/Dest/.foldify_backups/
   ```

3. **Manual recovery:**
   ```bash
   # Find and restore from backup
   find ~/Documents -name ".foldify_backups" -type d
   ```

### Enable backups

Always keep backups enabled:
```yaml
options:
  backup_conflicts: true
```

## Performance Issues

### Slow scanning of large directories

**Solutions:**

1. **Disable recursive scanning:**
   ```yaml
   sources:
     - path: ~/Downloads
       recursive: false  # Don't scan subdirectories
   ```

2. **Use specific patterns:**
   ```yaml
   sources:
     - path: ~/Downloads
       include_patterns: ["*.pdf"]  # Only PDFs
   ```

3. **Increase workers:**
   ```yaml
   options:
     max_workers: 8  # More parallel processing
   ```

### High memory usage

**Solutions:**

1. **Process in batches:**
   ```bash
   foldify run --profile school --limit 100
   ```

2. **Reduce AI content length:**
   ```yaml
   ai:
     max_content_length: 500
   ```

## Getting Help

If issues persist:

1. **Run with verbose logging:**
   ```bash
   foldify run --profile school --verbose 2>&1 | tee organizer.log
   ```

2. **Check the log file:**
   ```bash
   cat ~/.local/share/foldify/organizer.log
   ```

3. **Validate profile:**
   ```bash
   foldify validate school
   ```

4. **Report issues:**
   - GitHub Issues: https://github.com/YounessBerkia/Local-AI-Folder-Organizer/issues
   - Include: profile (sanitized), log output, error message
