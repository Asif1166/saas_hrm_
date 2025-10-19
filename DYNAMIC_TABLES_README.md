# Dynamic Table System Documentation

## Overview

The Dynamic Table System provides a comprehensive solution for managing table columns and permissions in a multi-tenant HRM/Payroll application. It allows organizations to control what data their employees can see and interact with based on their roles.

## Key Features

1. **Role-Based Column Permissions**: Control which columns each role can view, edit, or hide
2. **User-Specific Preferences**: Allow users to customize their table view
3. **Dynamic Column Visibility**: Show/hide columns in real-time
4. **Custom Column Ordering**: Reorder columns based on role or user preferences
5. **Serial Number Management**: Automatic column ordering and positioning
6. **Multi-Organization Support**: Each organization can have different table configurations

## Models

### DynamicTable
Defines the available tables in the system (employee_list, attendance_list, etc.)

### TableColumn
Defines individual columns for each table with properties like:
- Field name and display name
- Column type (text, number, date, image, etc.)
- Default visibility and ordering
- Sortable, searchable, and filterable flags

### RoleTablePermission
Controls table-level permissions (view, edit, delete, export) for each role

### RoleColumnPermission
Controls column-level permissions for each role:
- View permission
- Edit permission
- Hide permission
- Custom column ordering

### UserTablePreference
Stores user-specific table preferences:
- Column visibility settings
- Custom column order
- Page size preferences
- Saved filter configurations

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py makemigrations organization
python manage.py migrate
```

### 2. Setup Default Table Configurations
```bash
python manage.py setup_dynamic_tables
```

This command creates:
- Default table definitions
- Column configurations for employee_list
- Basic column permissions

### 3. Configure Organization-Specific Permissions

1. **Access Table Configuration**:
   - Navigate to Organization Dashboard
   - Click "Configure" → "Column Permissions"
   - Select the table you want to configure

2. **Setup Default Permissions**:
   - Click "Setup Default Permissions" button
   - This creates default permissions for all roles

3. **Customize Permissions**:
   - Modify table-level permissions (view, edit, delete, export)
   - Adjust column-level permissions for each role
   - Set custom column ordering per role

## Usage Examples

### Basic Employee List with Dynamic Columns

```python
# In your view
from organization.utils import DynamicTableManager

def employee_list(request):
    organization = request.organization
    
    # Check table access permission
    if not DynamicTableManager.can_user_access_table(request.user, organization, 'employee_list', 'view'):
        return redirect('dashboard')
    
    # Get user's accessible columns
    table_columns = DynamicTableManager.get_user_table_columns(
        request.user, organization, 'employee_list'
    )
    
    # Get user preferences
    user_preferences = DynamicTableManager.get_user_table_preferences(
        request.user, organization, 'employee_list'
    )
    
    context = {
        'table_columns': table_columns,
        'user_preferences': user_preferences,
        'can_edit': DynamicTableManager.can_user_access_table(request.user, organization, 'employee_list', 'edit'),
    }
    return render(request, 'hrm/employee_list.html', context)
```

### Template Usage

```html
<!-- Dynamic column headers -->
{% for column in table_columns %}
    <th data-column="{{ column.field_name }}">
        {{ column.display_name }}
    </th>
{% endfor %}

<!-- Dynamic column data -->
{% for column in table_columns %}
    <td data-column="{{ column.field_name }}">
        {% if column.column_type == 'image' %}
            <!-- Image rendering -->
        {% elif column.column_type == 'foreign_key' %}
            {{ employee|getattr:column.field_name|default:"-" }}
        {% else %}
            {{ employee|getattr:column.field_name|default:"-" }}
        {% endif %}
    </td>
{% endfor %}
```

### JavaScript Column Visibility

```javascript
// Toggle column visibility
function toggleColumnVisibility(columnName, isVisible) {
    const headerCells = document.querySelectorAll(`th[data-column="${columnName}"]`);
    const bodyCells = document.querySelectorAll(`td[data-column="${columnName}"]`);
    
    headerCells.forEach(cell => cell.style.display = isVisible ? '' : 'none');
    bodyCells.forEach(cell => cell.style.display = isVisible ? '' : 'none');
}

// Save user preferences
function saveColumnPreferences() {
    const preferences = {
        column_visibility: {},
        column_order: [],
        page_size: 20
    };
    
    document.querySelectorAll('.column-toggle').forEach(checkbox => {
        preferences.column_visibility[checkbox.dataset.column] = checkbox.checked;
    });
    
    // Send to server via AJAX
    fetch('/organization/tables/employee_list/preferences/save/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: new URLSearchParams({
            'column_visibility': JSON.stringify(preferences.column_visibility),
            'column_order': JSON.stringify(preferences.column_order),
            'page_size': preferences.page_size.toString()
        })
    });
}
```

## Permission System

### Table-Level Permissions
- **View**: Can see the table
- **Edit**: Can modify records
- **Delete**: Can delete records
- **Export**: Can export table data

### Column-Level Permissions
- **View**: Can see the column
- **Edit**: Can modify column data
- **Hide**: Can hide the column from view

### Role Hierarchy
1. **Super Admin**: Full access to everything
2. **Organization Admin**: Full access within organization
3. **HR Manager**: Limited admin access
4. **Manager**: Department-level access
5. **Employee**: Basic viewing access

## Customization

### Adding New Tables

1. **Create Table Definition**:
```python
# In setup_dynamic_tables.py
employee_table = DynamicTable.objects.create(
    name='custom_table',
    table_type='custom',
    display_name='Custom Table',
    description='Custom table for organization-specific data'
)
```

2. **Add Columns**:
```python
columns = [
    {'field_name': 'field1', 'display_name': 'Field 1', 'column_type': 'text', 'order': 1},
    {'field_name': 'field2', 'display_name': 'Field 2', 'column_type': 'number', 'order': 2},
]

for col_data in columns:
    TableColumn.objects.create(
        table=employee_table,
        **col_data
    )
```

3. **Update Views and Templates**:
- Add new view using DynamicTableManager
- Create template with dynamic column rendering
- Add URL patterns

### Adding New Column Types

1. **Update COLUMN_TYPES** in models.py:
```python
COLUMN_TYPES = [
    ('text', 'Text'),
    ('number', 'Number'),
    ('date', 'Date'),
    ('custom_type', 'Custom Type'),  # Add new type
]
```

2. **Update Template Rendering**:
```html
{% elif column.column_type == 'custom_type' %}
    <!-- Custom rendering logic -->
{% endif %}
```

## API Endpoints

### Table Configuration
- `GET /organization/tables/{table_name}/config/` - View table configuration
- `POST /organization/tables/{table_name}/permissions/` - Update permissions
- `POST /organization/tables/{table_name}/setup-defaults/` - Setup default permissions

### User Preferences
- `POST /organization/tables/{table_name}/preferences/save/` - Save user preferences
- `GET /organization/tables/{table_name}/preferences/get/` - Get user preferences
- `GET /organization/tables/{table_name}/columns/` - Get accessible columns

## Best Practices

1. **Security**: Always check permissions before displaying sensitive data
2. **Performance**: Use select_related for foreign key columns
3. **User Experience**: Provide clear feedback when permissions change
4. **Maintenance**: Regularly review and update column permissions
5. **Testing**: Test with different roles to ensure proper access control

## Troubleshooting

### Common Issues

1. **Columns not showing**: Check role permissions and user preferences
2. **JavaScript errors**: Ensure proper DOM element selection
3. **Permission denied**: Verify user role and organization membership
4. **Data not loading**: Check database queries and select_related usage

### Debug Mode

Enable debug logging in settings.py:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'dynamic_tables.log',
        },
    },
    'loggers': {
        'organization.utils': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Future Enhancements

1. **Column Filtering**: Advanced filtering options per column
2. **Export Customization**: Role-based export column selection
3. **Bulk Operations**: Mass update permissions
4. **Audit Trail**: Track permission changes
5. **Template Inheritance**: Reusable table templates
6. **Real-time Updates**: WebSocket-based live updates

This dynamic table system provides a robust foundation for managing data access in multi-tenant applications while maintaining flexibility and user experience.
