import os

root_files = [f for f in os.listdir('.') if f.endswith('.sql')]

print(f"🧹 Found {len(root_files)} SQL files in root directory.")

moved_count = 0
skipped_count = 0

for file in root_files:
    root_path = file
    subfolder_path = os.path.join('sql', file)
    
    if os.path.exists(subfolder_path):
        try:
            os.remove(root_path)
            print(f"✅ Deleted root file: {root_path} (already verified in sql/)")
            moved_count += 1
        except Exception as e:
            print(f"❌ Failed to delete {root_path}: {e}")
            skipped_count += 1
    else:
        print(f"⚠️  Skipped: {root_path} is NOT present in sql/ subdirectory. Copying first...")
        try:
            os.makedirs('sql', exist_ok=True)
            with open(root_path, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(subfolder_path, 'w', encoding='utf-8') as dst:
                dst.write(content)
            os.remove(root_path)
            print(f"✅ Copied and deleted: {root_path}")
            moved_count += 1
        except Exception as e:
            print(f"❌ Error copying/deleting {root_path}: {e}")
            skipped_count += 1

print(f"\n🎉 Cleanup complete! {moved_count} root SQL files removed. {skipped_count} skipped.")
