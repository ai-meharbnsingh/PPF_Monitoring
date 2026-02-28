# Issue Report: Workshop Dropdown Not Visible in "Add Member" Modal

## Problem Summary
When logged in as **super_admin**, clicking "Add Member" button on the Team page does NOT show a dropdown to select which workshop to assign the new user to.

## Expected Behavior
Super Admin should see:
1. A dropdown/select field labeled "Workshop *"
2. List of existing workshops to choose from
3. Able to create a user and assign them to any workshop

## Actual Behavior
The workshop dropdown is NOT visible. Only these fields show:
- Role radio buttons (staff/owner)
- Username
- Password
- First Name
- Last Name
- Email
- Phone

## Steps to Reproduce
1. Go to https://ppf-monitoring.vercel.app
2. Click "LOGIN"
3. Login with:
   - Username: `super_admin`
   - Password: `SuperAdmin@123`
4. Click "Team" in sidebar (or go to /admin/staff)
5. Click "Add Member" button
6. Observe: No workshop dropdown appears

## What Should Be Checked

### 1. Is `isSuperAdmin` true?
The code checks: `const isSuperAdmin = userRole === 'super_admin'`
- Check what `userRole` value is in the Redux store
- Check if `isSuperAdmin` is actually `true` when modal opens

### 2. Is workshops array populated?
The code loads workshops via: `workshopsApi.getAll()`
- Check if API call is made
- Check if workshops are returned (database has 1 workshop: "Delh_HUb")
- Check if `workshops` state is populated

### 3. Component Rendering
The dropdown only renders if: `{isSuperAdmin && (...)}`
- Verify `isSuperAdmin` is `true` during render
- Check if conditional rendering is working

### 4. API Endpoint
Backend endpoint: `GET /api/v1/workshops`
- Requires super_admin authentication
- Should return list of workshops

## Debug Code Added
```tsx
// Debug info displayed in modal:
<div className="text-xs text-gray-500">
  Role: {userRole} | SuperAdmin: {isSuperAdmin ? 'Yes' : 'No'} | Workshops: {workshops.length}
</div>

// Manual load button:
<button onClick={loadWorkshops}>↻ Load/Refresh Workshops</button>
```

## Database State
```sql
-- 1 workshop exists:
SELECT id, name FROM workshops;
-- Returns: id=3, name='Delh_HUb'
```

## Files Involved
- `frontend/src/pages/StaffPage.tsx` - Main component
- `frontend/src/api/workshops.ts` - API calls
- `frontend/src/store/slices/authSlice.ts` - User role from auth

## Hypothesis
The issue might be one of:
1. `userRole` from Redux is not exactly `'super_admin'` (maybe different case or format)
2. Workshops API call failing silently
3. Workshops array empty when component renders
4. Race condition - modal opens before workshops load

## What Antigravity Should Test
1. Open browser console
2. Check Redux DevTools - what is `state.auth.user.role`?
3. Check Network tab - is `/api/v1/workshops` being called?
4. Add breakpoint in StaffPage.tsx line 56: `const isSuperAdmin = ...`
5. Check if `workshops` array has items when modal opens
