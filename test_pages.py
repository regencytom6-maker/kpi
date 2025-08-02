import requests

print("Testing all admin pages...")

pages = [
    ("Dashboard", "/dashboard/admin-overview/"),
    ("Timeline", "/dashboard/admin/timeline/"),
    ("FGS Monitor", "/dashboard/admin/fgs-monitor/")
]

for name, url in pages:
    try:
        response = requests.get(f"http://127.0.0.1:8000{url}")
        status = "OK" if response.status_code == 200 else "ERROR"
        print(f"{name}: {status} ({response.status_code})")
    except Exception as e:
        print(f"{name}: ERROR - {str(e)}")

print("Testing completed!")
