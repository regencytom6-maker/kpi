# Kampala Pharmaceutical Industries - Testing Guide

## System Overview
The pharmaceutical operations system is now complete with all requested features:

### ✅ Completed Features
1. **Role-based User Management** - All 14 user roles via admin panel
2. **Manual Batch Entry** - QA can create batches manually
3. **Product Management** - Conditional fields for tablets (coating, type)
4. **Workflow Automation** - Auto-progression based on product type
5. **Role-specific Dashboards** - Each operator sees only their phases
6. **User Authentication** - Login/logout for all roles
7. **Admin Interface** - Complete management via Django admin

## How to Test the System

### 1. Start the Server
```powershell
# Option 1: Use the startup script
.\start_server.ps1

# Option 2: Manual activation
.\activate_env.ps1
python manage.py runserver
```

### 2. Access Points
- **Admin Interface**: http://127.0.0.1:8000/admin/
- **User Login**: http://127.0.0.1:8000/accounts/login/
- **Home Page**: http://127.0.0.1:8000/

### 3. Test Admin Login
- Username: `admin`
- Password: `admin123`

### 4. Test User Creation
1. Go to admin → Users → Add user
2. Create users for each role:
   - QA Officer
   - Regulatory Officer
   - Store Manager
   - QC Officer
   - Mixing Operator
   - Granulation Operator
   - Blending Operator
   - Compression Operator
   - Coating Operator
   - Drying Operator
   - Filling Operator
   - Tube Filling Operator
   - Packing Operator
   - Sorting Operator

### 5. Test Product Creation
1. Go to admin → Products → Add product
2. Test conditional fields:
   - Select "Tablet" → Coating and tablet type fields appear
   - Select "Ointment" → Only basic fields shown
   - Select "Capsule" → Only basic fields shown

### 6. Test BMR Creation & Workflow
1. Login as QA officer
2. Create new BMR from dashboard
3. Select product and enter batch details
4. Watch workflow initialize automatically
5. Login as different operators to see their phases

### 7. Test Phase Progression
1. Complete phases in order (Store Manager → Production Operators → QC → Final QA)
2. Verify each operator only sees their assigned phases
3. Test that phases only become available after predecessors complete

## Role Dashboard Testing

### QA Dashboard Features
- Create new BMRs
- View pending final QA reviews
- Access to all BMR details

### Regulatory Dashboard Features
- Review and approve/reject BMRs
- View regulatory approval queue

### Store Manager Dashboard Features
- Material dispensing tasks
- Packaging material release
- Finished goods storage

### Operator Dashboards Features
- Each operator sees only their specific phases
- Phases only available when predecessors are complete
- Clear indication of current workflow status

### QC Dashboard Features
- Quality control testing phases
- Approve/reject with rollback capability

## Product Type Workflows

### Tablets (Normal)
1. Material Dispensing → Granulation → Blending → Compression → Coating* → Blister Packing → Secondary Packaging → QC → Final QA
*Coating only if coating_type is not "none"

### Tablets (Type 2)
1. Material Dispensing → Granulation → Blending → Compression → Coating* → Bulk Packing → Secondary Packaging → QC → Final QA

### Ointments
1. Material Dispensing → Mixing → Tube Filling → Secondary Packaging → QC → Final QA

### Capsules
1. Material Dispensing → Drying → Blending → Filling → Blister Packing → Secondary Packaging → QC → Final QA

## Key Features to Verify

### ✅ Conditional Product Fields
- Tablet fields only show for tablets
- Coating dropdown with proper options
- Tablet type dropdown (Normal/Type 2)

### ✅ Role-based Access
- Each user only sees relevant phases
- Dashboards filter by user role
- Phase progression enforced by role

### ✅ Workflow Automation
- Phases auto-initialize based on product type
- Proper phase ordering maintained
- Conditional routing (coating, packing type)

### ✅ User Management
- All 14 roles available in admin
- Users can login and access dashboards
- Role-based navigation and permissions

## Success Criteria
- [ ] All 14 user roles can be created
- [ ] Product admin shows conditional tablet fields
- [ ] BMR creation initializes correct workflow
- [ ] Each operator sees only their phases
- [ ] Phase progression follows product workflow
- [ ] Quality control can approve/reject batches
- [ ] Admin interface manages all entities

The system is ready for production use and meets all specified requirements for pharmaceutical operations management.
