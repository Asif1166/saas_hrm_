import json
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from organization.decorators import organization_member_required


def handle_bulk_delete(request, model, model_name):
    """Generic soft/hard delete for multiple model objects"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        delete_type = data.get('type', 'soft')  # 'soft' or 'hard'

        if not ids:
            return JsonResponse({'success': False, 'message': f'No {model_name}s selected.'})

        queryset = model.objects.all_with_deleted().filter(id__in=ids, organization=request.organization)
        count = queryset.count()

        if delete_type == 'soft':
            for obj in queryset:
                obj.delete()
            message = f'{count} {model_name}(s) moved to trash successfully.'
        elif delete_type == 'hard':
            for obj in queryset:
                obj.hard_delete()
            message = f'{count} {model_name}(s) permanently deleted successfully.'
        else:
            return JsonResponse({'success': False, 'message': 'Invalid delete type.'})

        return JsonResponse({'success': True, 'message': message})

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@organization_member_required
def trash_list_view(request, model, template_name, context_name):
    """Generic view for listing soft-deleted objects"""
    organization = request.organization
    deleted_objects = model.objects.only_deleted().filter(organization=organization)

    paginator = Paginator(deleted_objects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, template_name, {
        'organization': organization,
        'page_obj': page_obj,
        context_name: page_obj
    })


@login_required
@organization_member_required
def restore_objects_view(request, model, model_name):
    """Generic restore view"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    try:
        data = json.loads(request.body)
        ids = data.get('ids', [])
        if not ids:
            return JsonResponse({'success': False, 'message': f'No {model_name}s selected.'})

        restored_count = model.objects.only_deleted().filter(
            id__in=ids, organization=request.organization
        ).update(deleted_at=None)

        return JsonResponse({
            'success': True,
            'message': f'{restored_count} {model_name}(s) restored successfully.'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})