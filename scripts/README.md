# Usage

Update CONTENT_DIR and CENTRAL_IMAGES_DIR at the top of the file.

Run python3 migrate_to_bundles.py to check the dry-run output.

Set DRY_RUN = False and run it again to apply the changes.

## How to Run It Safely

1. **Back up your project** (or commit your current state with `git add . && git commit -m "Before bundle migration"`).
2. Edit the top 3 paths in `migrate_to_bundles.py` to match your actual folders:

- `CONTENT_DIR`: Where your `.md` files live (e.g., `./content/docs`).
- `CENTRAL_IMAGES_DIR`: Where your unorganized images are currently stored.

3. Run a **Dry Run** first to verify what gets matched:

```bash
python3 migrate_to_bundles.py
```

4. Once the terminal output looks right, change `DRY_RUN = False` inside the script and run it again:

```bash
python3 migrate_to_bundles.py
```

---

### Result Structure

For `2009-05-16.md`, the script generates:

```text
content/docs/2009/05/
├── _index.md
└── 2009-05-16/
    ├── index.md
    └── images/
        ├── 2009-05-16_01.jpg
        └── 2009-05-16_02.jpg
```

_(Note: Because the script uses `shutil.copy2()`, your original files in `CENTRAL_IMAGES_DIR` stay untouched as a backup until you're ready to delete them.)_
