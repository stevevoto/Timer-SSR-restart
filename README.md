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

