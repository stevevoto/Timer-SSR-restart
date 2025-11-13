
#!/usr/bin/env python3

# =============================================================================
#  Script:        mist_gateway_reboot.py
#  Description:   Interactive Mist gateway reboot tool that loads credentials
#                 from 'Token-Org-URL.txt', shows all gateway devices (with
#                 site names), lets you select one or more devices, schedule
#                 a reboot (absolute or relative time), and then sends the
#                 appropriate Mist API restart calls.
#  Author:        Stephen Voto
#  Created:       Nov 13, 2025
#
#  DISCLAIMER:
#  This tool is provided "AS IS" for lab, testing, and operational assistance.
#  It is not an official Juniper/Mist product and carries no warranty or
#  support obligation of any kind.
#
#  You are solely responsible for reviewing, testing, and validating this code
#  before use in any environment. Use at your own risk. The author
#  assumes no liability for outages, data loss, misconfiguration, or any other
#  impact resulting from the use of this script.
# =============================================================================

import requests
import datetime
import time
import sys
import readline
from typing import Any, Dict, List, Optional

TOKEN_FILE = "Token-Org-URL.txt"


def load_credentials():
    """
    Load Mist API credentials from Token-Org-URL.txt (key=value format).
      token=...
      org_id=...
      base_url=...

    Normalizes base_url so final value always ends with /api/v1.
    """
    print("Loading Mist API credentials from Token-Org-URL.txt...")
    token = org_id = base_url = None

    try:
        with open(TOKEN_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == 'token':
                        token = value
                    elif key == 'org_id':
                        org_id = value
                    elif key == 'base_url':
                        base_url = value
    except Exception as e:
        print(f"Error reading credentials file: {e}")
        sys.exit(1)

    if not token or not org_id or not base_url:
        print("Credentials file is missing required fields (token, org_id, base_url).")
        sys.exit(1)

    # Normalize base_url to always be .../api/v1
    base_url = base_url.strip().rstrip('/')
    if base_url.endswith("/api/v1"):
        base_url = base_url[:-len("/api/v1")]
    base_url = base_url + "/api/v1"

    print("Credentials loaded successfully.")
    print(f"Normalized base_url: {base_url}")
    return token, org_id, base_url


def make_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Accept": "application/json, application/vnd.api+json",
        "Content-Type": "application/json",
    }


def get_sites(org_id: str, token: str, base_url: str) -> List[Dict[str, Any]]:
    """
    Fetch list of sites to map site_id -> site_name.
    """
    url = f"{base_url.rstrip('/')}/orgs/{org_id}/sites"
    headers = make_headers(token)
    params = {"limit": 1000}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Warning: failed to fetch sites list: {e}")
        return []

    try:
        data = resp.json()
    except Exception as e:
        print(f"Warning: failed to parse sites response JSON: {e}")
        return []

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "results" in data:
        return data.get("results", [])
    print("Warning: unexpected sites response format.")
    return []


def fetch_gateway_inventory(headers: Dict[str, str],
                            base_url: str,
                            org_id: str,
                            site_name_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Fetch org inventory for gateways and return only those with a site_id.
    Also prints the device inventory with site names.
    """
    inventory_url = f"{base_url}/orgs/{org_id}/inventory?type=gateway"
    print(f"\nFetching device inventory from {inventory_url}")
    try:
        resp = requests.get(inventory_url, headers=headers, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch inventory: {e}")
        return []

    try:
        devices = resp.json()
    except Exception as e:
        print(f"Error parsing inventory response: {e}")
        return []

    gateways = [d for d in devices if d.get("site_id")]
    if not gateways:
        print("No gateway devices with site_id found.")
        return []

    print("\nDevice Inventory (gateways with a site_id):")
    for idx, dev in enumerate(gateways, 1):
        name = dev.get('name', dev.get('mac', 'unnamed'))
        site_id = dev.get('site_id', '')
        # Prefer site_name from inventory if present, else from org sites list
        site_name = dev.get('site_name') or site_name_map.get(site_id, 'unknown-site')
        # stash site_name so we can re-use it when printing selected devices
        dev['_site_name'] = site_name
        # Site name in the first column after the index
        print(
            f"{idx}. {site_name}  {name}  MAC: {dev['mac']}  "
            f"site_id: {site_id}  id: {dev['id']}"
        )
    return gateways


def select_devices(gateways: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Allow user to select one or more gateways by index.
    Returns:
      - list of selected device dicts
      - [] if user gave invalid/empty selection but wants to continue
      - None if user entered 'q' to exit the program
    """
    if not gateways:
        return []

    while True:
        choice = input(
            "\nEnter the number(s) of device(s) to reboot "
            "(e.g., 1 or 1,3) or 'q' to quit: "
        ).strip()

        if not choice:
            print("No input detected. Please enter device number(s) or 'q' to quit.")
            continue

        if choice.lower() in ("q", "quit", "x", "exit"):
            print("Exiting program.")
            return None

        try:
            indices = sorted(
                set(int(x.strip()) - 1 for x in choice.split(',') if x.strip())
            )
            if any(i < 0 or i >= len(gateways) for i in indices):
                raise ValueError()
            selected_devices = [gateways[i] for i in indices]
            break
        except Exception:
            print("Invalid input. Please try again.")
            continue

    print("\nSelected device(s) to reboot:")
    for dev in selected_devices:
        site_name = dev.get('_site_name', 'unknown-site')
        print(
            f" - {dev.get('name', dev['mac'])} "
            f"(MAC: {dev['mac']}, site: {site_name}, "
            f"site_id: {dev['site_id']}, id: {dev['id']})"
        )

    confirm = input("Proceed with these device(s)? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Reboot cancelled.")
        return []

    return selected_devices


def schedule_reboot_time() -> Optional[datetime.datetime]:
    """
    Ask user how to schedule the reboot:
      1. Absolute time
      2. Relative offset

    Returns a datetime or None if cancelled.
    """
    while True:
        print("\nSchedule the reboot:")
        print("  1. Absolute time (MM:DD:YYYY HH:MM:SS)")
        print("  2. Relative offset from now (HH:MM:SS)")
        print("  q. Cancel")
        method = input("Choose option 1 or 2 (or 'q' to cancel): ").strip().lower()

        if method in ('q', 'quit', 'x', 'exit'):
            print("Scheduling cancelled.")
            return None

        if method == '1':
            abs_time_str = input(
                "Enter the absolute date and time (MM:DD:YYYY HH:MM:SS): "
            ).strip()
            try:
                schedule_time = datetime.datetime.strptime(
                    abs_time_str, "%m:%d:%Y %H:%M:%S"
                )
                return schedule_time
            except Exception:
                print("Invalid format. Please try again.")
        elif method == '2':
            offset = input("Enter the offset from now (HH:MM:SS): ").strip()
            try:
                h, m, s = map(int, offset.split(':'))
                schedule_time = datetime.datetime.now() + datetime.timedelta(
                    hours=h, minutes=m, seconds=s
                )
                return schedule_time
            except Exception:
                print("Invalid format. Please try again.")
        else:
            print("Invalid choice. Please select 1, 2, or 'q' to cancel.")


def perform_reboots(selected_devices: List[Dict[str, Any]],
                    headers: Dict[str, str],
                    base_url: str) -> bool:
    """
    Schedule and perform the reboot(s) for selected devices.
    Blocks until scheduled time, then issues POST /restart for each.

    Returns True if any reboot was attempted, False otherwise.
    """
    if not selected_devices:
        return False

    schedule_time = schedule_reboot_time()
    if schedule_time is None:
        # user cancelled scheduling
        return False

    now = datetime.datetime.now()
    delay = max(0, (schedule_time - now).total_seconds())
    print(f"\nCurrent time:        {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Scheduled reboot at: {schedule_time.strftime('%Y-%m-%d %H:%M:%S')} "
          f"(in ~{int(delay)} seconds)")

    if delay > 0:
        print(f"Waiting for scheduled time... (~{int(delay)} seconds)")
        time.sleep(delay)

    print("\n*** Initiating reboot now ***\n")

    attempted = 0
    for dev in selected_devices:
        site_id = dev['site_id']
        device_id = dev['id']
        reboot_url = f"{base_url}/sites/{site_id}/devices/{device_id}/restart"

        name = dev.get('name', dev.get('mac', 'unnamed'))
        print(f"Sending reboot command for {name} (MAC: {dev['mac']})")
        print(f"  POST {reboot_url}")
        try:
            resp = requests.post(reboot_url, headers=headers, timeout=30)
            attempted += 1
            if resp.status_code == 200:
                print("  Success: Reboot command accepted (HTTP 200).")
            else:
                print(f"  Error: Reboot failed (HTTP {resp.status_code})")
                print(f"  Response body: \n{resp.text}\n")
        except Exception as e:
            print(f"  Exception during reboot: {e}\n")

    if attempted:
        print("Reboot process completed.")
        return True

    print("No reboot commands were sent.")
    return False


def main():
    token, org_id, base_url = load_credentials()
    headers = make_headers(token)

    # Build a map from site_id -> site_name to show human-friendly names
    sites = get_sites(org_id, token, base_url)
    site_name_map = {
        s.get("id"): s.get("name", "unknown-site")
        for s in sites
        if s.get("id")
    }

    # Main loop: always show inventory first, then selection, then reboot, then ask to continue.
    while True:
        gateways = fetch_gateway_inventory(headers, base_url, org_id, site_name_map)
        if not gateways:
            # No gateways or inventory fetch failed
            ans = input("\nNo gateways available. Press Enter to retry, or 'q' to quit: ").strip().lower()
            if ans in ("q", "quit", "x", "exit"):
                print("Exiting.")
                break
            else:
                continue

        selected_devices = select_devices(gateways)
        if selected_devices is None:
            # User hit 'q' at selection prompt -> exit program
            break
        if not selected_devices:
            # User cancelled/declined after seeing devices -> just loop back
            continue

        did_reboot = perform_reboots(selected_devices, headers, base_url)

        # After a completed reboot cycle, ask if they want to do more
        if did_reboot:
            ans = input("\nDo you want to reboot more devices? (y/N): ").strip().lower()
            if ans not in ("y", "yes"):
                print("Exiting.")
                break
        else:
            # Reboot was cancelled during scheduling; just loop back
            continue


if __name__ == "__main__":
    main()

