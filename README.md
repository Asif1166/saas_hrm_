# HRM & Payroll Management SaaS System

A comprehensive multi-tenant SaaS application for Human Resource Management and Payroll processing built with Django.

## Features

### Multi-Tenant Architecture
- **Single Database Multi-Tenancy**: One database with organization-based data isolation
- **Super Admin**: Platform owner who can create and manage organizations
- **Organization Admin**: Each organization has its own admin
- **Role-based Access Control**: Different permissions for different user types

### User Roles
1. **Super Admin**: Platform owner, can create organizations and manage the entire system
2. **Organization Admin**: Manages their specific organization's data
3. **Employee**: Regular employees within an organization

### Core Modules
- **Authentication**: User management with role-based access
- **Organization**: Multi-tenant organization management
- **HRM**: Human Resource Management (Employees, Departments, Attendance, Leave Management)
- **Payroll**: Payroll processing (Salary structures, Payslips, Allowances, Deductions)

## Project Structure

```
payroll_hrm_management/
├── authentication/          # User authentication and management
├── organization/            # Organization and multi-tenancy management
├── hrm/                    # Human Resource Management
├── payroll/                # Payroll Management
├── core/                   # Django project settings
├── templates/              # HTML templates
├── static/                 # Static files (CSS, JS, Images)
└── manage.py              # Django management script
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Django 5.2+
- SQLite (default) or PostgreSQL

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd payroll_hrm_management
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create super admin user**
   ```bash
   python manage.py create_super_admin
   ```
   Or use custom parameters:
   ```bash
   python manage.py create_super_admin --username admin --email admin@example.com --password your_password
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Login page: http://127.0.0.1:8000/login/
   - Django Admin: http://127.0.0.1:8000/admin/

## Usage

### Super Admin Workflow
1. Login with super admin credentials
2. Access the Super Admin Dashboard
3. Create new organizations
4. Each organization gets its own admin user
5. Monitor all organizations from the dashboard

### Organization Admin Workflow
1. Login with organization admin credentials
2. Access the Organization Dashboard
3. Manage employees, departments, attendance, and payroll
4. All data is isolated to their organization

### Employee Workflow
1. Login with employee credentials
2. Access employee dashboard (to be implemented)
3. View personal information, attendance, payslips, etc.

## Database Models

### Authentication Models
- **User**: Custom user model with roles (super_admin, organization_admin, employee)

### Organization Models
- **Organization**: Tenant organizations with contact info, settings, and limits
- **OrganizationMembership**: User-organization relationships with admin privileges

### HRM Models
- **Department**: Organization-specific departments
- **Employee**: Employee profiles linked to users and organizations
- **Attendance**: Attendance tracking for employees
- **LeaveRequest**: Leave management system

### Payroll Models
- **PayrollPeriod**: Payroll periods for each organization
- **SalaryStructure**: Employee salary structures
- **Payslip**: Individual payslips for employees
- **Allowance/Deduction**: Allowance and deduction types

## Security Features

- **Data Isolation**: All data is filtered by organization
- **Role-based Access**: Decorators ensure proper access control
- **Middleware**: Organization context added to all requests
- **Authentication**: Secure login/logout system

## API Endpoints

### Authentication
- `GET/POST /login/` - User login
- `GET /logout/` - User logout
- `GET /dashboard/` - Role-based dashboard redirect

### Super Admin
- `GET /super-admin/` - Super admin dashboard
- `GET /super-admin/organizations/` - List organizations
- `GET/POST /super-admin/organizations/create/` - Create organization
- `GET /super-admin/organizations/<id>/` - Organization details
- `GET/POST /super-admin/organizations/<id>/update/` - Update organization

### Organization Admin
- `GET /organization/dashboard/` - Organization dashboard

### HRM
- `GET /hrm/` - HRM dashboard
- `GET /hrm/employees/` - Employee list
- `GET /hrm/departments/` - Department list
- `GET /hrm/attendance/` - Attendance list
- `GET /hrm/leaves/` - Leave requests

### Payroll
- `GET /payroll/` - Payroll dashboard
- `GET /payroll/periods/` - Payroll periods
- `GET /payroll/payslips/` - Payslips
- `GET /payroll/salary-structures/` - Salary structures

## Development

### Adding New Features
1. Create models with `BaseOrganizationModel` for data isolation
2. Add views with appropriate decorators (`@organization_member_required`)
3. Create templates in the appropriate app directory
4. Update URL patterns

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Super Admin
```bash
python manage.py create_super_admin
```

## Deployment

### Production Settings
1. Change `DEBUG = False`
2. Set proper `SECRET_KEY`
3. Configure database (PostgreSQL recommended)
4. Set up static file serving
5. Configure email settings
6. Set up proper logging

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/dbname
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team.
