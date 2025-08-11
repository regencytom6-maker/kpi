from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import BMR, BMRMaterial
from .serializers import (
    BMRCreateSerializer, BMRDetailSerializer, BMRListSerializer,
    BMRMaterialSerializer, ProductSerializer
)
from .forms import BMRCreateForm
from products.models import Product
from workflow.services import WorkflowService

@login_required
def create_bmr_view(request):
    """Simple form view for QA to create BMR with manual batch number"""
    if request.user.role != 'qa':
        messages.error(request, 'Only QA officers can create BMRs')
        return redirect('admin:index')
    
    if request.method == 'POST':
        form = BMRCreateForm(request.POST)
        if form.is_valid():
            bmr = form.save(commit=False)
            bmr.created_by = request.user
            try:
                bmr.save()
            except Exception as e:
                from django.db import IntegrityError
                if isinstance(e, IntegrityError) and 'UNIQUE constraint failed' in str(e):
                    messages.error(request, f'A BMR with this batch number already exists. Please use a unique batch number.')
                    return render(request, 'bmr/create_bmr.html', {
                        'form': form,
                        'title': 'Create New BMR'
                    })
                else:
                    raise
            # Initialize workflow for this BMR
            try:
                WorkflowService.initialize_workflow_for_bmr(bmr)
                workflow_status = WorkflowService.get_workflow_status(bmr)
                messages.success(
                    request, 
                    f'BMR created successfully with batch number {bmr.batch_number}. '
                    f'Next phase: {workflow_status["next_phase"].phase.get_phase_name_display() if workflow_status["next_phase"] else "None"}'
                )
            except Exception as e:
                messages.warning(
                    request,
                    f'BMR created with batch number {bmr.batch_number}, but workflow initialization failed: {e}'
                )
            return redirect('bmr:detail', bmr.id)
    else:
        form = BMRCreateForm()
    
    return render(request, 'bmr/create_bmr.html', {
        'form': form,
        'title': 'Create New BMR'
    })

@login_required
def bmr_list_view(request):
    """List view for BMRs with role-based filtering"""
    bmrs = BMR.objects.select_related('product', 'created_by', 'approved_by').all().order_by('-created_date')
    
    # Filter based on user role
    if request.user.role == 'qa':
        # QA can see all BMRs
        pass
    elif request.user.role == 'regulatory':
        # Regulatory can see BMRs pending approval or approved
        bmrs = bmrs.filter(status__in=['pending_approval', 'approved'])
    elif request.user.role == 'qc':
        # QC can see approved BMRs
        bmrs = bmrs.filter(status='approved')
    else:
        # Operators can see approved BMRs
        bmrs = bmrs.filter(status='approved')
    
    return render(request, 'bmr/bmr_list.html', {
        'bmrs': bmrs,
        'title': 'BMR List'
    })

@login_required
def bmr_detail_view(request, bmr_id):
    """Detail view for a specific BMR with workflow information"""
    bmr = get_object_or_404(BMR.objects.select_related('product', 'created_by', 'approved_by'), id=bmr_id)
    
    # Check permissions
    if request.user.role not in ['qa', 'regulatory', 'qc'] and bmr.status != 'approved':
        messages.error(request, 'You do not have permission to view this BMR')
        return redirect('home')
    
    # Get related materials
    materials = BMRMaterial.objects.filter(bmr=bmr)
    
    # Get workflow status
    workflow_status = WorkflowService.get_workflow_status(bmr)
    
    # Get phases for current user
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    return render(request, 'bmr/bmr_detail.html', {
        'bmr': bmr,
        'materials': materials,
        'workflow_status': workflow_status,
        'user_phases': user_phases,
        'title': f'BMR Details - {bmr.bmr_number}'
    })

class BMRViewSet(viewsets.ModelViewSet):
    """ViewSet for BMR operations"""
    queryset = BMR.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'product', 'created_by']
    search_fields = ['bmr_number', 'batch_number', 'product__product_name']
    ordering_fields = ['created_date', 'planned_start_date', 'status']
    ordering = ['-created_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BMRCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return BMRDetailSerializer
        return BMRListSerializer
    
    def get_queryset(self):
        """Filter BMRs based on user role"""
        user = self.request.user
        queryset = BMR.objects.select_related('product', 'created_by', 'approved_by')
        
        # Role-based filtering
        if user.role == 'qa':
            # QA can see all BMRs
            return queryset
        elif user.role == 'regulatory':
            # Regulatory can see submitted BMRs
            return queryset.filter(status__in=['submitted', 'approved', 'rejected'])
        else:
            # Other users see BMRs relevant to their operations
            return queryset.filter(status__in=['approved', 'in_production', 'completed'])
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit_for_approval(self, request, pk=None):
        """Submit BMR for regulatory approval"""
        bmr = self.get_object()
        
        if request.user.role != 'qa':
            return Response(
                {'error': 'Only QA can submit BMRs for approval'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'draft':
            return Response(
                {'error': 'Only draft BMRs can be submitted'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'submitted'
        bmr.save()
        
        return Response({'message': 'BMR submitted for approval'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve BMR (Regulatory role)"""
        bmr = self.get_object()
        
        if request.user.role != 'regulatory':
            return Response(
                {'error': 'Only regulatory can approve BMRs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'submitted':
            return Response(
                {'error': 'Only submitted BMRs can be approved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'approved'
        bmr.approved_by = request.user
        bmr.approved_date = timezone.now()
        bmr.regulatory_comments = request.data.get('comments', '')
        bmr.save()
        
        # Create initial workflow phases using the proper service
        from workflow.services import WorkflowService
        WorkflowService.initialize_workflow_for_bmr(bmr)
        
        return Response({'message': 'BMR approved successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject BMR (Regulatory role)"""
        bmr = self.get_object()
        
        if request.user.role != 'regulatory':
            return Response(
                {'error': 'Only regulatory can reject BMRs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if bmr.status != 'submitted':
            return Response(
                {'error': 'Only submitted BMRs can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bmr.status = 'rejected'
        bmr.regulatory_comments = request.data.get('comments', '')
        bmr.save()
        
        return Response({'message': 'BMR rejected'})

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for product information (for BMR creation)"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_type', 'dosage_form']
    search_fields = ['product_code', 'product_name']
    ordering = ['product_code']

@login_required
def start_phase_view(request, bmr_id, phase_name):
    """Start a specific phase for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Check if user has permission to start this phase
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    if not user_phases.filter(phase__phase_name=phase_name, status='pending').exists():
        messages.error(request, f'You cannot start the {phase_name} phase at this time.')
        return redirect('bmr:detail', bmr_id)
    
    # Check if prerequisites are met
    if not WorkflowService.can_start_phase(bmr, phase_name):
        messages.error(request, f'Cannot start {phase_name.replace("_", " ").title()} phase - prerequisite phases must be completed first.')
        return redirect('bmr:detail', bmr_id)
    
    # Start the phase
    execution = WorkflowService.start_phase(bmr, phase_name, request.user)
    
    if execution:
        messages.success(
            request, 
            f'Started {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}'
        )
    else:
        messages.error(request, f'Failed to start {phase_name} phase.')
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qa':
        return redirect('dashboards:qa_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    elif request.user.role == 'store_manager':
        return redirect('dashboards:store_dashboard')
    elif request.user.role == 'packaging_store':
        return redirect('dashboards:packaging_dashboard')
    elif request.user.role == 'finished_goods_store':
        return redirect('dashboards:finished_goods_dashboard')
    else:
        return redirect('dashboards:operator_dashboard')

@login_required
def complete_phase_view(request, bmr_id, phase_name):
    """Complete a specific phase for a BMR"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Check if user has permission to complete this phase
    user_phases = WorkflowService.get_phases_for_user_role(bmr, request.user.role)
    
    if not user_phases.filter(phase__phase_name=phase_name, status='in_progress').exists():
        messages.error(request, f'You cannot complete the {phase_name} phase at this time.')
        return redirect('bmr:detail', bmr_id)
    
    # Get comments from request
    comments = request.GET.get('comments', '') or request.POST.get('comments', '')
    
    # Complete the phase
    next_phase = WorkflowService.complete_phase(bmr, phase_name, request.user, comments)
    
    if next_phase:
        messages.success(
            request, 
            f'Completed {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}. '
            f'Next phase: {next_phase.phase.phase_name.replace("_", " ").title()}'
        )
    else:
        messages.success(
            request, 
            f'Completed {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}.'
        )
    
    # Update BMR status based on phase
    if phase_name == 'regulatory_approval':
        bmr.status = 'approved'
        bmr.approved_by = request.user
        bmr.approved_date = timezone.now()
        bmr.save()
    elif phase_name == 'final_qa':
        bmr.status = 'completed'
        bmr.actual_completion_date = timezone.now()
        bmr.save()
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qa':
        return redirect('dashboards:qa_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    elif request.user.role == 'store_manager':
        return redirect('dashboards:store_dashboard')
    elif request.user.role == 'packaging_store':
        return redirect('dashboards:packaging_dashboard')
    elif request.user.role == 'finished_goods_store':
        return redirect('dashboards:finished_goods_dashboard')
    else:
        return redirect('dashboards:operator_dashboard')

@login_required
def reject_phase_view(request, bmr_id, phase_name):
    """Reject a phase (mainly for regulatory and QC)"""
    bmr = get_object_or_404(BMR, id=bmr_id)
    
    # Only regulatory and QC can reject
    if request.user.role not in ['regulatory', 'qc']:
        messages.error(request, 'You do not have permission to reject phases.')
        return redirect('bmr:detail', bmr_id)
    
    # Get rejection reason
    comments = request.GET.get('comments', '') or request.POST.get('comments', '')
    if not comments:
        messages.error(request, 'Rejection reason is required.')
        return redirect('bmr:detail', bmr_id)
    
    # Handle QC failure with rollback for different QC phases
    if request.user.role == 'qc' and phase_name in ['post_compression_qc', 'post_mixing_qc', 'post_blending_qc']:
        try:
            # Mark the QC phase as failed with comments
            from workflow.models import BatchPhaseExecution
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='in_progress'
            )
            execution.status = 'failed'
            execution.completed_by = request.user
            execution.completed_date = timezone.now()
            
            # Determine rollback phase based on QC type
            rollback_mapping = {
                'post_compression_qc': 'blending',
                'post_mixing_qc': 'mixing',
                'post_blending_qc': 'blending'
            }
            rollback_phase = rollback_mapping[phase_name]
            
            execution.operator_comments = f"QC FAILED - ROLLBACK TO {rollback_phase.upper()}: {comments}"
            execution.save()
            
            # Trigger rollback to appropriate phase
            rollback_success = WorkflowService.handle_qc_failure_rollback(bmr, phase_name, rollback_phase)
            
            if rollback_success:
                messages.warning(
                    request,
                    f'{phase_name.replace("_", " ").title()} failed for BMR {bmr.batch_number}. '
                    f'Batch has been rolled back to {rollback_phase.replace("_", " ")} phase. Reason: {comments}'
                )
            else:
                messages.error(request, 'Failed to process QC rollback. Please contact system administrator.')
            
        except Exception as e:
            messages.error(request, f'Failed to process QC failure: {e}')
    
    # Handle Final QA failure with rollback to respective packing phase
    elif phase_name == 'final_qa' and request.user.role == 'qa':
        try:
            # Determine rollback phase based on product type and packing
            product_type = bmr.product.product_type
            
            # Get the last completed packing phase to rollback to
            from workflow.models import BatchPhaseExecution
            packing_phases = ['blister_packing', 'bulk_packing', 'secondary_packaging']
            last_packing_phase = None
            
            for packing_phase in reversed(packing_phases):  # Check in reverse order
                try:
                    packing_execution = BatchPhaseExecution.objects.get(
                        bmr=bmr,
                        phase__phase_name=packing_phase,
                        status='completed'
                    )
                    last_packing_phase = packing_phase
                    break
                except BatchPhaseExecution.DoesNotExist:
                    continue
            
            if last_packing_phase:
                # Mark Final QA as failed
                execution = BatchPhaseExecution.objects.get(
                    bmr=bmr,
                    phase__phase_name=phase_name,
                    status='in_progress'
                )
                execution.status = 'failed'
                execution.completed_by = request.user
                execution.completed_date = timezone.now()
                execution.operator_comments = f"FINAL QA FAILED - ROLLBACK TO {last_packing_phase.upper()}: {comments}"
                execution.save()
                
                # Trigger rollback to last packing phase
                rollback_success = WorkflowService.handle_qc_failure_rollback(bmr, phase_name, last_packing_phase)
                
                if rollback_success:
                    messages.warning(
                        request,
                        f'Final QA failed for BMR {bmr.batch_number}. '
                        f'Batch has been rolled back to {last_packing_phase.replace("_", " ")} phase. Reason: {comments}'
                    )
                else:
                    messages.error(request, 'Failed to process Final QA rollback. Please contact system administrator.')
            else:
                messages.error(request, 'Cannot determine packing phase for rollback.')
                
        except Exception as e:
            messages.error(request, f'Failed to process Final QA failure: {e}')
    
    else:
        # Handle other phase rejections (original logic)
        try:
            from workflow.models import BatchPhaseExecution
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='in_progress'
            )
            execution.status = 'failed'
            execution.completed_by = request.user
            execution.completed_date = timezone.now()
            execution.operator_comments = f"REJECTED: {comments}"
            execution.save()
            
            # Update BMR status for regulatory rejection
            if phase_name == 'regulatory_approval':
                bmr.status = 'rejected'
                bmr.approved_by = request.user
                bmr.approved_date = timezone.now()
                bmr.save()
            
            messages.warning(
                request,
                f'Rejected {phase_name.replace("_", " ").title()} phase for BMR {bmr.batch_number}. '
                f'Reason: {comments}'
            )
            
        except Exception as e:
            messages.error(request, f'Failed to reject phase: {e}')
    
    # Redirect back to appropriate dashboard
    if request.user.role == 'regulatory':
        return redirect('dashboards:regulatory_dashboard')
    elif request.user.role == 'qc':
        return redirect('dashboards:qc_dashboard')
    else:
        return redirect('bmr:detail', bmr_id)
