"""
Quick Property Reset - Clean only properties and related data
Run this script to quickly reset all properties while keeping users intact
"""

import os
import json


def quick_property_reset():
    """Fast reset of properties and related data only"""

    print("🧹 Quick Property Reset - Cleaning properties...")

    # Files to reset to empty
    files_to_reset = [
        "data/properties.json",
        "data/documents.json",
        "data/chats.json",
        "data/buying_transactions.json",
        "data/buying_chats.json"
    ]

    # Reset each file to empty JSON
    for file_path in files_to_reset:
        if os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f, indent=2)
            print(f"✅ Reset: {file_path}")
        else:
            print(f"⚠️  Creating: {file_path}")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump({}, f, indent=2)

    # Clean buyer interests (remove property references)
    buyers_file = "data/buyers.json"
    if os.path.exists(buyers_file):
        with open(buyers_file, 'r') as f:
            buyers = json.load(f)

        for buyer_id, buyer_data in buyers.items():
            buyer_data["interested_properties"] = []
            buyer_data["reserved_properties"] = []

        with open(buyers_file, 'w') as f:
            json.dump(buyers, f, indent=2)
        print(f"✅ Cleaned buyer interests: {buyers_file}")

    # Clean notary work lists (remove property references)
    notaries_file = "data/notaries.json"
    if os.path.exists(notaries_file):
        with open(notaries_file, 'r') as f:
            notaries = json.load(f)

        for notary_id, notary_data in notaries.items():
            notary_data["checked_prop_list"] = []
            notary_data["properties_to_check"] = []
            notary_data["buyers_to_check"] = []

        with open(notaries_file, 'w') as f:
            json.dump(notaries, f, indent=2)
        print(f"✅ Cleaned notary work lists: {notaries_file}")

    # Clean uploaded files but keep directories
    file_dirs = [
        "data/files/documents",
        "data/files/photos",
        "data/files/additional_docs",
        "data/files/buying_documents"
    ]

    for dir_path in file_dirs:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(f"✅ Cleaned files in: {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created directory: {dir_path}")

    print("\n🎉 QUICK PROPERTY RESET COMPLETE!")
    print("✅ All properties deleted")
    print("✅ All documents deleted")
    print("✅ All chats deleted")
    print("✅ All buying transactions deleted")
    print("✅ All uploaded files deleted")
    print("✅ User accounts preserved")
    print("\n🚀 You can now start adding properties fresh!")


if __name__ == "__main__":
    print("🧹 Quick Property Reset Tool")
    print("=" * 30)
    print("This will delete:")
    print("- All properties")
    print("- All documents")
    print("- All chats")
    print("- All buying transactions")
    print("- All uploaded files")
    print("\nThis will KEEP:")
    print("- Agent accounts")
    print("- Buyer accounts")
    print("- Notary accounts")

    confirm = input("\nProceed? (y/N): ").strip().lower()

    if confirm in ['y', 'yes']:
        quick_property_reset()
    else:
        print("❌ Reset cancelled")