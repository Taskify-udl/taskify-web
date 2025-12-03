# taskify_app/adapters.py

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import CustomUser

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        # 1. Create the base user (username, email, etc.)
        user = super().save_user(request, sociallogin, form)

        # 2. Retrieve bridge data from the session
        signup_data = request.session.get('signup_context', {})

        if signup_data:
            # Save first_name and last_name if available
            full_name = signup_data.get('full_name', '')
            if full_name:
                name_parts = full_name.strip().split(' ', 1)
                user.first_name = name_parts[0] if len(name_parts) > 0 else ''
                user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            # Map frontend role values to database enum values
            role_mapping = {
                'client': CustomUser.Roles.CUSTOMER,
                'provider': CustomUser.Roles.PROVIDER,
            }
            
            frontend_role = signup_data.get('role')
            if frontend_role:
                # Map the frontend role to the database role
                user.role = role_mapping.get(frontend_role, CustomUser.Roles.CUSTOMER)
            
            # Handle provider-specific data
            provider_sub_role = signup_data.get('provider_sub_role')
            if user.role == CustomUser.Roles.PROVIDER and provider_sub_role:
                if provider_sub_role == 'freelancer':
                    user.role = CustomUser.Roles.FREELANCER
                elif provider_sub_role == 'company':
                    user.role = CustomUser.Roles.COMPANY_ADMIN
                    # Save company info if provided
                    company_name = signup_data.get('company_name')
                    company_tax_id = signup_data.get('company_tax_id')
                    if company_name:
                        user.company_name = company_name
                    if company_tax_id:
                        user.tax_id = company_tax_id
                
            user.save()
        
        return user
