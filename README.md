# Timer-SSR-restart
Interactive Mist gateway reboot tool that loads credentials from 'Token-Org-URL.txt', shows all gateway devices (with site names), lets you select one or more devices, schedule a reboot (absolute or relative time)

# Mist Gateway Reboot Tool

Interactive Mist gateway reboot tool that loads credentials from `Token-Org-URL.txt`, shows all gateway devices (with site names), lets you select one or more devices, schedule a reboot (absolute or relative time), and then sends the appropriate Mist API restart calls.

> **Author:** Stephen Voto  
> **Status:** Lab / tools use – not an official product

---

## Features

- Reads Mist credentials from `Token-Org-URL.txt`:
  - `token`
  - `org_id`
  - `base_url`
- Normalizes `base_url` so it always uses `https://api.mist.com/api/v1`.
- Fetches **all gateway devices** in the org inventory.
- Shows a friendly inventory list with:
  - Site name (e.g., `Seattle`, `Boston`)
  - Device name
  - MAC
  - `site_id`
  - Device `id`
- Lets you select **one or multiple devices** to reboot.
- Supports **two scheduling modes**:
  - Absolute time: `MM:DD:YYYY HH:MM:SS`
  - Relative offset: `HH:MM:SS` from now
- Issues `POST /api/v1/sites/{site_id}/devices/{device_id}/restart` for each device.
- After a reboot cycle, you can:
  - Reboot more devices, or  
  - Quit cleanly.

---

## Requirements

- Python 3.7+
- `requests` library

Install `requests`:

```bash
pip install requests

# Mist Gateway Reboot Tool

Interactive Mist gateway reboot tool that loads credentials from `Token-Org-URL.txt`, shows all gateway devices (with site names), lets you select one or more devices, schedule a reboot (absolute or relative time), and then sends the appropriate Mist API restart calls.

> **Script:** `Timer-SSR-restart.py`  
> **Author:** Stephen Voto  

---

## Token-Org-URL.txt Format

The script expects a file named `Token-Org-URL.txt` in the same directory, with at least these fields:

```text
token=YOUR_MIST_API_TOKEN
org_id=YOUR_ORG_ID
base_url=https://api.mist.com/api/v1
base_url can be either:

## Usage

From the directory containing the script and Token-Org-URL.txt:

python3 mist_gateway_reboot.py

Example Flow

Script loads credentials and normalizes base_url.

Fetches org gateway inventory and prints something like:

Device Inventory (gateways with a site_id):
1. Seattle  seattle-ssr-1  MAC: 02000117f2d8  site_id: a618679d-...  id: 00000000-...
2. Boston   boston-ssr-1   MAC: 02000117f3aa  site_id: b7123abc-...  id: 00000000-...


You enter one or more indices (e.g., 1 or 1,2).

Confirm the devices.

Choose scheduling:

Absolute: 01:31:2026 23:45:00

Relative: 00:00:10

Script waits until the scheduled time and then sends the appropriate restart calls.

To quit at selection

Enter q at the device selection prompt to exit the program.

Notes & Behavior

If the inventory fetch fails or no gateways are found, the script lets you retry or quit.

Site names are pulled from:

The inventory (site_name field) when present, or

GET /orgs/{org_id}/sites as a fallback map.

Disclaimer

This tool is provided "AS IS" for lab, testing, and operational assistance.
It is not an official Juniper/Mist product and carries no warranty or support obligation.

You are solely responsible for reviewing, testing, and validating this code before use in any  environment. Use at your own risk. The author assumes no liability for outages, data loss, misconfiguration, or any other impact resulting from the use of this script.

https://api.mist.com

https://api.mist.com/api/v1

The script normalizes it so it always uses the /api/v1 form.
