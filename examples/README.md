# Example Profiles

Copy these examples to `~/.config/foldify/profiles/` and customize for your needs.

## Available Examples

- `school.yaml.example` - Organize school files by subject
- `work.yaml.example` - Work document organization
- `desktop-cleanup.yaml.example` - Downloads/Desktop cleanup
- `ai-smart.yaml.example` - AI-powered classification

## Creating Your Own

1. Copy an example: `cp school.yaml.example ~/.config/foldify/profiles/school.yaml`
2. Edit paths to match your system
3. Customize rules for your files
4. Test with `foldify validate school`
5. Preview with `foldify run --profile school --dry-run` before executing
