import os
import sys
import django
from django.test import Client
from django.urls import reverse
from bs4 import BeautifulSoup

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

def test_admin_timeline():
    """Test the admin timeline page to ensure it has been updated with the new tabular layout."""
    print("Testing Admin Timeline Page...")
    
    # Create a test client
    client = Client()
    
    try:
        # Try to access the admin timeline page
        url = reverse('dashboards:admin_timeline')
        print(f"Accessing URL: {url}")
        response = client.get(url)
        
        if response.status_code == 200:
            print("✅ Successfully accessed the admin timeline page")
        else:
            print(f"❌ Failed to access admin timeline page. Status code: {response.status_code}")
            return False
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for the existence of the tabular timeline elements
        timeline_table = soup.find('table', {'class': 'timeline-table', 'id': 'timelineTable'})
        if timeline_table:
            print("✅ Found the timeline table element")
        else:
            print("❌ Could not find timeline table element")
            return False
        
        # Check for table headers
        table_headers = timeline_table.find_all('th')
        expected_headers = ["Batch Number", "Product Name", "Type", "Created", "Current Phase", 
                            "Cycle Time", "Status", "Actions"]
        
        found_headers = [header.text.strip() for header in table_headers if header.text.strip()]
        print(f"Found headers: {found_headers}")
        
        # Check if most of the expected headers are present
        matches = sum(1 for header in expected_headers if any(header in found for found in found_headers))
        if matches >= len(expected_headers) / 2:  # At least half of the headers should match
            print(f"✅ Found expected table headers: {matches}/{len(expected_headers)}")
        else:
            print(f"❌ Missing many expected table headers. Found only {matches}/{len(expected_headers)}")
            print(f"   Found headers: {found_headers}")
            return False
        
        # Check for search and filter elements
        search_input = soup.find('input', {'id': 'searchTimeline'})
        if search_input:
            print("✅ Found search input element")
        else:
            print("❌ Could not find search input element")
            return False
        
        filter_selects = soup.find_all('select', {'class': 'filter-select'})
        if len(filter_selects) >= 2:
            print(f"✅ Found {len(filter_selects)} filter select elements")
        else:
            print(f"❌ Found only {len(filter_selects)} filter select elements, expected at least 2")
            return False
        
        # Check for sidebar
        sidebar = soup.find('div', {'class': 'sidebar'})
        if sidebar:
            print("✅ Found sidebar navigation")
            
            # Check for sidebar menu items
            menu_items = sidebar.find_all('a')
            if len(menu_items) >= 5:
                print(f"✅ Found {len(menu_items)} sidebar menu items")
            else:
                print(f"❌ Found only {len(menu_items)} sidebar menu items, expected at least 5")
                return False
        else:
            print("❌ Could not find sidebar navigation")
            return False
        
        # Check for expand/collapse functionality
        expand_buttons = soup.find_all('a', {'class': 'expand-row'})
        if expand_buttons:
            print(f"✅ Found {len(expand_buttons)} expand/collapse buttons")
        else:
            print("❌ Could not find expand/collapse buttons for phase details")
            return False
        
        # Check for phase details sections
        phase_details = soup.find_all('div', {'class': 'phase-details'})
        if phase_details:
            print(f"✅ Found {len(phase_details)} phase detail sections")
        else:
            print("❌ Could not find phase detail sections")
            return False
        
        # Check for pagination
        pagination = soup.find('nav', {'aria-label': 'Timeline pagination'})
        if pagination:
            print("✅ Found pagination navigation")
        else:
            print("⚠️ Could not find pagination navigation (this may be ok if there are few items)")
        
        print("\nAdmin Timeline Test Result: PASS ✅")
        return True
    
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_admin_timeline()
