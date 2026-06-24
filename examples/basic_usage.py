"""A runnable example of contractguard catching API drift.

Run it with:

    python examples/basic_usage.py
"""

import contractguard as cg


def main() -> None:
    # Imagine these are two known-good responses from an API you depend on.
    good_samples = [
        {
            "user": {"id": 1, "name": "ana", "email": "ana@example.com"},
            "items": [{"sku": "A1", "price": 9.99}],
        },
        {
            "user": {"id": 2, "name": "bob"},  # no email this time
            "items": [{"sku": "B2", "price": 4.50}],
        },
    ]

    # Learn the contract. Because 'email' is missing from the second sample,
    # it's treated as optional and won't be flagged later.
    contract = cg.learn(good_samples)
    print("Learned a contract from", len(good_samples), "samples.\n")

    # A month later, the API changes shape under you.
    drifted_payload = {
        "user": {"id": 3, "name": "cleo", "age": "unknown", "phone": "555-0100"},
        "items": [{"sku": "C3", "price": "free"}],
    }

    report = contract.check(drifted_payload)

    if report.drifted:
        print("Drift detected:\n")
        print(report)
    else:
        print("No drift — payload matches the contract.")


if __name__ == "__main__":
    main()
