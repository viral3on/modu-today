"""Compatibility entry point for the retired external-news collector.

Kept so old manual commands cannot resume collection or overwrite content.
The site build no longer reads or publishes news/data.json.
"""

def main():
    print("Automatic news collection ended on 2026-11-07. No data fetched or changed.")

if __name__ == "__main__":
    main()
