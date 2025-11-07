from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Count
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
import logging
from rest_framework.permissions import AllowAny
logger = logging.getLogger(__name__)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions, status
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count
import time
from django.shortcuts import render
from django.contrib import messages
import logging
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions, status
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
################################################################################################################################
from .models import (
    User,
    Category,
    LostItem,
    FoundItem, 
    Claim, 
    Notification,
    ImageSearchLog   
)
################################################################################################################################
from .serializers import *
#####################################################################################
from .models import ImageFeature, generate_image_embedding, LostItem, FoundItem ####========> new updated
import numpy as np  ##############==> new updated==>
##############################################################################################################################################################
#########################################################################################################################################################
def home(request):
    context = {
        
    }
    # Render the HTML template index.html with the data in the context variable
    return render(request, 'home.html', context=context)
###########################################################################################################################################################
#############################################################################################################################################################
class AuthViewSet(viewsets.GenericViewSet):
    """
    Authentication ViewSet for user registration and login
    """
    permission_classes = [AllowAny]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'update_password':
            return UpdatePasswordSerializer
        return RegisterSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        User registration endpoint with automatic token creation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Get tokens after user creation
        tokens_serializer = self.get_serializer(user)
        
        return Response({
            'message': 'User registered successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'tower_number': user.tower_number,
                'room_number': user.room_number,
                'profile_image': user.profile_image.url if user.profile_image else None,
            },
            'tokens': tokens_serializer.get_tokens(user)
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        User login endpoint using email and password with automatic token creation
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        return Response({
            'message': 'Login successful!',
            'user': validated_data['user'],
            'tokens': validated_data['tokens'],
            'redirect_url': validated_data['redirect_url']
        }, status=status.HTTP_200_OK)
###########################################################################
# Custom Permissions
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.user_type == 'admin':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user

class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'admin'
#################################################################################################################################################
#################################################################################################################################################
class UserProfileViewSet(viewsets.GenericViewSet,
                        mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin):
    """
    User Profile ViewSet for managing user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update current user profile
        """
        if request.method == 'GET':
            serializer = self.get_serializer(self.get_object())
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(
                self.get_object(), 
                data=request.data, 
                partial=partial
            )
            serializer.is_valid(raise_exception=True)
            
            # Handle file upload separately
            if 'profile_image' in request.FILES:
                serializer.validated_data['profile_image'] = request.FILES['profile_image']
            
            self.perform_update(serializer)
            
            return Response({
                'message': 'Profile updated successfully!',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
    ############################################################################################################################
    ########################################################################
    # Update Password (requires old password)
    ########################################################################
    @action(detail=False, methods=['put'], serializer_class=UpdatePasswordSerializer, permission_classes=[])
    def password(self, request):
        """
        Update user password using email and old password
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password updated successfully!'
        }, status=status.HTTP_200_OK)

    ########################################################################
    # Forgot Password (reset with email only)
    ########################################################################
    @action(detail=False, methods=['put'], serializer_class=ForgotPasswordSerializer, permission_classes=[])
    def forgot_password(self, request):
        """
        Reset user password using email only
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Password reset successfully!'
        }, status=status.HTTP_200_OK)
    ##################################################################################
    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_account(self, request):
        """
        Delete the currently authenticated user's account
        """
        user = request.user
        user.delete()

        return Response({
            'message': 'Your account has been deleted successfully.'
        }, status=status.HTTP_200_OK)
    ##############################################################################################################################
    @action(detail=False, methods=['get'])
    def details(self, request):
        """
        Get current user details with profile
        """
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)
    ###############################################################################################################################
    def perform_update(self, serializer):
        serializer.save()
########################################################################################################################################################################################################
#####################################################################################################################################################################################################
#####################################################################Additional convenience views for backward compatibility####################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user details (for backward compatibility)
    """
    from .serializers import UserProfileSerializer
    user = request.user
    serializer = UserProfileSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
###############################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """
    Get all users API (alternative implementation)
    """
    from .serializers import UserListSerializer
    
    users = User.objects.filter(is_active=True)
    
    # Apply filters
    tower_number = request.GET.get('tower_number')
    user_type = request.GET.get('user_type')
    
    if tower_number:
        users = users.filter(tower_number=tower_number)
    if user_type:
        users = users.filter(user_type=user_type)
    
    serializer = UserListSerializer(users, many=True)
    return Response({
        'count': users.count(),
        'users': serializer.data
    }, status=status.HTTP_200_OK)
##################################
#################################################################################################################################################
#################################################################################################################################################
#####################################################################################
# ===========================================
# CATEGORY VIEWSET
# ===========================================
class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category management viewset.
    - All authenticated users can list/retrieve categories.
    - Only admins can create/update/delete.
    """
    queryset = Category.objects.all().order_by('id')  # ✅ Fix UnorderedObjectListWarning
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsAdminOnly]
        return [permission() for permission in permission_classes]
###################################################################################################################################################################################################
##############################################################################################################################################################################################
# ===========================================
# LOST ITEM VIEWSET
# ===========================================
class LostItemViewSet(viewsets.ModelViewSet):
    """
    Lost item management.
    - Admin can view all items.
    - Resident sees only their own.
    - Returns success message on create.
    """
    serializer_class = LostItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ✅ Use select_related to reduce DB hits (performance)
        base_qs = LostItem.objects.select_related('user', 'category').order_by('-created_at')

        if user.user_type == 'admin':
            return base_qs
        else:
            # ✅ Resident: show only own lost items
            return base_qs.filter(user=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            # Pass user in context instead of save parameter
            lost_item = serializer.save()
            
            # Get the serialized data for response
            response_serializer = self.get_serializer(lost_item)

            return Response(
                {
                    "success": True,
                    "message": "Lost item added successfully!",
                    "data": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        except serializers.ValidationError as e:
            # Handle validation errors specifically
            logger.error(f"Validation error creating Lost Item: {e}")
            return Response(
                {
                    "success": False,
                    "message": "Please check your input data.",
                    "errors": e.detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error creating Lost Item: {e}")
            return Response(
                {
                    "success": False,
                    "message": "An unexpected error occurred. Please try again.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_lost_items(self, request):
        """
        Resident: show only own lost items.
        Admin: show all.
        """
        user = request.user
        if user.user_type == 'admin':
            items = LostItem.objects.all().order_by('-created_at')
        else:
            items = LostItem.objects.filter(user=user).order_by('-created_at')

        if not items.exists():
            return Response(
                {"message": "No lost items found."},
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_found(self, request, pk=None):
        """
        Mark item as found — allowed for owner or admin.
        """
        item = self.get_object()
        if item.user != request.user and request.user.user_type != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        item.status = 'found'
        item.save()
        return Response({"detail": "Item marked as found."})
#######################################################################################################################################################################################################
###################################################################################################################################################################################################
# FoundItem ViewSet
class FoundItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoundItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Allow all authenticated users (residents & admins) to view all Found Items.
        """
        return FoundItem.objects.all()

    def perform_create(self, serializer):
        """
        Automatically attach the current user as the creator when adding a found item.
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_found_items(self, request):
        """
        View only the found items created by the current user.
        """
        items = FoundItem.objects.filter(user=request.user)
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_returned(self, request, pk=None):
        """
        Mark a found item as returned (allowed for item owner or admin).
        """
        item = self.get_object()
        if item.user != request.user and getattr(request.user, 'user_type', None) != 'admin':
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)
        item.status = 'returned'
        item.save()
        return Response({"detail": "Item marked as returned."})
######################################################################################################################################################################################################
# Claim ViewSet
class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return Claim.objects.all()
        return Claim.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOnly])
    def approve_claim(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'approved'
        claim.resolved_at = timezone.now()
        claim.save()
        
        # Update found item status
        claim.found_item.status = 'returned'
        claim.found_item.save()
        
        return Response({"detail": "Claim approved successfully."})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOnly])
    def reject_claim(self, request, pk=None):
        claim = self.get_object()
        claim.status = 'rejected'
        claim.resolved_at = timezone.now()
        claim.save()
        return Response({"detail": "Claim rejected."})

#####################################################################################
# Notification ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({"unread_count": count})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"detail": "Notification marked as read."})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


##################################################################################################################################################################################################
##################################################################################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manual_image_search(request):
    """
    AI-like Smart Image Search API
    --------------------------------
    Fully robust version with:
      ✅ Strict category validation
      ✅ Block unrelated category data
      ✅ Category-level existence check for Lost/Found
      ✅ Clean metadata + helpful message
    """
    import re, time
    from django.db.models import Q

    start_time = time.time()
    serializer = ManualImageSearchSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    search_query = (data.get('search_query') or '').strip()
    search_type = (data.get('search_type') or '').strip().lower()
    color_filters = (data.get('color_filters') or '').strip()
    category_filters = (data.get('category_filters') or '').strip()
    max_results = data.get('max_results', 50)

    search_terms = [t.strip().lower() for t in re.split(r'[, ]+', search_query) if t.strip()]
    color_terms = [c.strip().lower() for c in re.split(r'[, ]+', color_filters) if c.strip()]
    category_terms = [c.strip().lower() for c in re.split(r'[, ]+', category_filters) if c.strip()]

    LostModel = LostItem
    FoundModel = FoundItem
    CategoryModel = Category

    lost_qs, found_qs = LostModel.objects.none(), FoundModel.objects.none()
    matched_category = None
    message = None

    # ---------------------- CATEGORY VALIDATION ----------------------
    if category_filters and category_filters.lower() != 'all':
        matched_category = CategoryModel.objects.filter(name__iexact=category_filters).first()

        # Category does not exist at all
        if not matched_category:
            return Response({
                "count": 0,
                "results": [],
                "message": f"This category '{category_filters}' does not exist.",
                "search_metadata": {
                    "query": search_query or "N/A",
                    "type": search_type or "auto",
                    "filters_applied": {
                        "colors": color_filters or "N/A",
                        "categories": category_filters or "Invalid / Not Found"
                    },
                    "category_exists": False,
                    "results_count": 0,
                    "search_duration_seconds": round(time.time() - start_time, 3),
                    "max_results": max_results
                }
            })

        # Category exists, now check if any item exists under it
        has_lost = LostModel.objects.filter(category=matched_category).exists()
        has_found = FoundModel.objects.filter(category=matched_category).exists()

        # If no item exists for selected search_type, block results
        if search_type == 'lost' and not has_lost:
            return Response({
                "count": 0,
                "results": [],
                "message": f"No Lost items found under category '{matched_category.name}'.",
                "category_details": CategorySerializer(matched_category).data,
                "search_metadata": {
                    "query": search_query or "N/A",
                    "type": "lost",
                    "filters_applied": {
                        "colors": color_filters or "N/A",
                        "categories": matched_category.name
                    },
                    "category_exists": True,
                    "results_count": 0,
                    "search_duration_seconds": round(time.time() - start_time, 3),
                    "max_results": max_results
                }
            })

        if search_type == 'found' and not has_found:
            return Response({
                "count": 0,
                "results": [],
                "message": f"No Found items found under category '{matched_category.name}'.",
                "category_details": CategorySerializer(matched_category).data,
                "search_metadata": {
                    "query": search_query or "N/A",
                    "type": "found",
                    "filters_applied": {
                        "colors": color_filters or "N/A",
                        "categories": matched_category.name
                    },
                    "category_exists": True,
                    "results_count": 0,
                    "search_duration_seconds": round(time.time() - start_time, 3),
                    "max_results": max_results
                }
            })

        # If type=all and no data exists at all
        if search_type == 'all' and not (has_lost or has_found):
            return Response({
                "count": 0,
                "results": [],
                "message": f"No Lost or Found items exist under category '{matched_category.name}'.",
                "category_details": CategorySerializer(matched_category).data,
                "search_metadata": {
                    "query": search_query or "N/A",
                    "type": "all",
                    "filters_applied": {
                        "colors": color_filters or "N/A",
                        "categories": matched_category.name
                    },
                    "category_exists": True,
                    "results_count": 0,
                    "search_duration_seconds": round(time.time() - start_time, 3),
                    "max_results": max_results
                }
            })

    # ---------------------- FLEXIBLE SEARCH LOGIC ----------------------
    if not (search_query or search_type or category_filters or color_filters):
        lost_qs, found_qs = LostModel.objects.all(), FoundModel.objects.all()

    elif category_filters.lower() == 'all':
        lost_qs, found_qs = LostModel.objects.all(), FoundModel.objects.all()
        search_type = 'all'

    elif search_type == 'lost' and not search_query:
        lost_qs = LostModel.objects.all()

    elif color_filters and not (search_query or category_filters or search_type):
        lost_qs, found_qs = LostModel.objects.all(), FoundModel.objects.all()

    elif category_filters and not (search_query or search_type):
        lost_qs, found_qs = LostModel.objects.all(), FoundModel.objects.all()

    else:
        if search_type == 'lost':
            base_qs = LostModel.objects.all()
        elif search_type == 'found':
            base_qs = FoundModel.objects.all()
        else:
            lost_qs, found_qs = LostModel.objects.all(), FoundModel.objects.all()
            search_type = 'all'
            base_qs = None

        if base_qs is not None:
            queryset = base_qs

            # Text Search
            if search_terms:
                text_q = Q()
                for term in search_terms:
                    text_q |= (
                        Q(title__icontains=term)
                        | Q(description__icontains=term)
                        | Q(search_tags__icontains=term)
                        | Q(color_tags__icontains=term)
                        | Q(material_tags__icontains=term)
                        | Q(brand__icontains=term)
                        | Q(color__icontains=term)
                        | Q(size__icontains=term)
                        | Q(category__name__icontains=term)
                        | Q(lost_location__icontains=term)
                    )
                queryset = queryset.filter(text_q)

            # Color Filters
            if color_terms:
                cq = Q()
                for c in color_terms:
                    cq |= Q(color_tags__icontains=c) | Q(color__icontains=c)
                queryset = queryset.filter(cq)

            # Category Filter (strict)
            if matched_category:
                queryset = queryset.filter(category=matched_category)
            elif category_terms:
                cat_q = Q()
                for cat in category_terms:
                    cat_q |= Q(category__name__iexact=cat)
                queryset = queryset.filter(cat_q)

            if search_type == 'lost':
                lost_qs = queryset
            elif search_type == 'found':
                found_qs = queryset

    # ---------------------- Combine Results ----------------------
    lost_items = list(lost_qs[:max_results])
    found_items = list(found_qs[:max_results])

    combined_items = sorted(
        list(lost_items) + list(found_items),
        key=lambda x: getattr(x, "created_at", None) or 0,
        reverse=True
    )

    results = combined_items[:max_results]
    search_duration = time.time() - start_time

    # ---------------------- Log Search ----------------------
    ImageSearchLog.objects.create(
        user=request.user,
        search_type=search_type or 'auto',
        search_query=search_query or 'N/A',
        color_filters=color_filters,
        category_filters=category_filters,
        results_count=len(results),
        search_duration=search_duration
    )

    # ---------------------- Serialize Results ----------------------
    lost_data = LostItemSerializer(
        [r for r in results if isinstance(r, LostModel)],
        many=True, context={'request': request}
    ).data

    found_data = FoundItemSerializer(
        [r for r in results if isinstance(r, FoundModel)],
        many=True, context={'request': request}
    ).data

    results_data = lost_data + found_data

    category_data = CategorySerializer(matched_category).data if matched_category else None

    # ---------------------- Final Response ----------------------
    return Response({
        "count": len(results_data),
        "next": None,
        "previous": None,
        "results": results_data,
        "message": message or "Results found successfully.",
        "search_metadata": {
            "query": search_query or "N/A",
            "type": search_type or "auto",
            "filters_applied": {
                "colors": color_filters or "N/A",
                "categories": category_filters or "N/A"
            },
            "category_details": category_data,
            "category_exists": bool(matched_category),
            "results_count": len(results_data),
            "search_duration_seconds": round(search_duration, 3),
            "max_results": max_results
        }
    })
##########################################################################################################################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard(request):
    """
    User dashboard for residents.
    Shows only the user's own Lost & Found items and related stats.
    If a resident user has not added any Lost or Found items, those lists are not shown.
    """
    user = request.user

    # ✅ Only allow for resident users
    if not hasattr(user, 'role') or user.role.lower() != 'resident':
        return Response({"detail": "Access restricted. Only resident users can view this dashboard."},
                        status=status.HTTP_403_FORBIDDEN)

    # --- Base statistics ---
    stats = {
        'total_lost_items': LostItem.objects.filter(user=user).count(),
        'total_found_items': FoundItem.objects.filter(user=user).count(),
        'total_claims': Claim.objects.filter(user=user).count(),
        'pending_claims': Claim.objects.filter(user=user, status='pending').count(),
        'approved_claims': Claim.objects.filter(user=user, status='approved').count(),
        'unread_notifications': Notification.objects.filter(user=user, is_read=False).count(),
    }

    # --- Conditionally include Lost and Found lists ---
    recent_activities = []

    user_lost_items = LostItem.objects.filter(user=user).order_by('-created_at')
    user_found_items = FoundItem.objects.filter(user=user).order_by('-created_at')
    user_claims = Claim.objects.filter(user=user).order_by('-created_at')

    # ✅ Only include if user has Lost items
    if user_lost_items.exists():
        for item in user_lost_items[:5]:
            recent_activities.append({
                'type': 'lost_item',
                'title': item.title,
                'status': item.status,
                'date': item.created_at,
                'id': item.id
            })

    # ✅ Only include if user has Found items
    if user_found_items.exists():
        for item in user_found_items[:5]:
            recent_activities.append({
                'type': 'found_item',
                'title': item.title,
                'status': item.status,
                'date': item.created_at,
                'id': item.id
            })

    # ✅ Always include claims (if any)
    if user_claims.exists():
        for claim in user_claims[:5]:
            recent_activities.append({
                'type': 'claim',
                'title': f"Claim for {claim.found_item.title}" if claim.found_item else "Claim",
                'status': claim.status,
                'date': claim.created_at,
                'id': claim.id
            })

    # Sort activities (latest first)
    if recent_activities:
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        stats['recent_activities'] = recent_activities[:10]
    else:
        stats['recent_activities'] = []

    # --- Serializer output ---
    serializer = DashboardStatsSerializer(data=stats)
    serializer.is_valid(raise_exception=False)

    return Response(serializer.data)
###########################################################################################################################################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics"""
    
    stats = {
        'total_lost_items': LostItem.objects.count(),
        'total_found_items': FoundItem.objects.count(),
        'total_claims': Claim.objects.count(),
        'pending_claims': Claim.objects.filter(status='pending').count(),
        'approved_claims': Claim.objects.filter(status='approved').count(),
        'total_users': User.objects.count(),
        'verified_lost_items': LostItem.objects.filter(is_verified=True).count(),
        'verified_found_items': FoundItem.objects.filter(is_verified=True).count(),
        'returned_items': FoundItem.objects.filter(status='returned').count(),
        'claimed_items': Claim.objects.filter(status='approved').count(),
        'user_registrations_today': User.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
    }
    
    # Recent activities across the system
    recent_lost = LostItem.objects.all().order_by('-created_at')[:5]
    recent_found = FoundItem.objects.all().order_by('-created_at')[:5]
    recent_claims = Claim.objects.all().order_by('-created_at')[:5]
    recent_users = User.objects.all().order_by('-created_at')[:5]
    
    recent_activities = []
    
    for item in recent_lost:
        recent_activities.append({
            'type': 'lost_item',
            'title': item.title,
            'user': item.user.username,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })
    
    for item in recent_found:
        recent_activities.append({
            'type': 'found_item',
            'title': item.title,
            'user': item.user.username,
            'status': item.status,
            'date': item.created_at,
            'id': item.id
        })
    
    for claim in recent_claims:
        recent_activities.append({
            'type': 'claim',
            'title': f"Claim by {claim.user.username}",
            'status': claim.status,
            'date': claim.created_at,
            'id': claim.id
        })
    
    for user in recent_users:
        recent_activities.append({
            'type': 'user_registration',
            'title': f"New user: {user.username}",
            'user_type': user.user_type,
            'date': user.created_at,
            'id': user.id
        })
    
    # Sort by date
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:15]
    
    stats['recent_activities'] = recent_activities
    
    serializer = AdminDashboardStatsSerializer(stats)
    return Response(serializer.data)

#####################################################################################
# Item Verification APIs (Admin only)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_lost_item(request, item_id):
    try:
        item = LostItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
        # Create notification for user
        Notification.objects.create(
            user=item.user,
            notification_type='system',
            title='Item Verified',
            message=f'Your lost item "{item.title}" has been verified by admin.',
            lost_item=item
        )
        
        return Response({"detail": "Item verified successfully."})
    except LostItem.DoesNotExist:
        return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminOnly])
def verify_found_item(request, item_id):
    try:
        item = FoundItem.objects.get(id=item_id)
        item.is_verified = True
        item.save()
        
        # Create notification for user
        Notification.objects.create(
            user=item.user,
            notification_type='system',
            title='Item Verified',
            message=f'Your found item "{item.title}" has been verified by admin.',
            found_item=item
        )
        
        return Response({"detail": "Item verified successfully."})
    except FoundItem.DoesNotExist:

        return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)
################################################################################################################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def image_based_search(request):
    """
    Upload an image and find visually similar lost/found items using deep embeddings.
    """
    uploaded_image = request.FILES.get('image')
    search_type = request.data.get('search_type', 'found')  # or 'lost'
    max_results = int(request.data.get('max_results', 10))

    if not uploaded_image:
        return Response({"error": "No image provided."}, status=status.HTTP_400_BAD_REQUEST)

    # Generate embedding for the uploaded image
    query_emb = generate_image_embedding(uploaded_image)
    if query_emb is None:
        return Response({"error": "Could not process image."}, status=status.HTTP_400_BAD_REQUEST)

    query_vec = np.frombuffer(query_emb, dtype=np.float32)

    # Retrieve stored embeddings of same item type
    db_features = ImageFeature.objects.filter(item_type=search_type)
    similarities = []
    for feature in db_features:
        vec = np.frombuffer(feature.embedding, dtype=np.float32)
        sim = np.dot(query_vec, vec)  # cosine similarity
        similarities.append((feature.item_id, sim))

    # Sort by similarity and pick top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_ids = [s[0] for s in similarities[:max_results]]

    # Fetch matched items
    if search_type == 'lost':
        matched_items = LostItem.objects.filter(id__in=top_ids)
        serializer = LostItemSerializer(matched_items, many=True, context={'request': request})
    else:
        matched_items = FoundItem.objects.filter(id__in=top_ids)
        serializer = FoundItemSerializer(matched_items, many=True, context={'request': request})

    return Response({
        'search_metadata': {
            'search_type': search_type,
            'results_count': len(serializer.data)
        },
        'results': serializer.data
    }, status=status.HTTP_200_OK)


















