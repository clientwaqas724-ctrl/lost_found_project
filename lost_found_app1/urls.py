from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import (
    CategoryViewSet,
    LostItemViewSet,
    FoundItemViewSet,
    ClaimViewSet,
    NotificationViewSet,
    manual_image_search,
    user_dashboard,
    admin_dashboard,
    verify_lost_item,
    verify_found_item,
    image_based_search,
    get_image_features,
    regenerate_image_features
)

# Create router and register viewsets
router = DefaultRouter()
router1 = DefaultRouter()

router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'profile', views.UserProfileViewSet, basename='profile')

################################################################################################
router1.register(r'categories', CategoryViewSet, basename='category')
router1.register(r'lost-items', LostItemViewSet, basename='lostitem')
router1.register(r'found-items', FoundItemViewSet, basename='founditem')
router1.register(r'claims', ClaimViewSet, basename='claim')
router1.register(r'notifications', NotificationViewSet, basename='notification')
################################################################################################

urlpatterns = [  
    # Include ViewSet routes
    path('api/', include(router.urls)),
    
    # JWT token refresh
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Backward compatibility endpoints
    path('api/me/', views.get_current_user, name='current-user'),
    path('api/users/', views.get_all_users, name='all-users'),
    
    ####################################################################################################
    path('', include(router1.urls)),
    
    ######################################################################################################
    path('dashboard/user/', user_dashboard, name='user-dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin-dashboard'),
    
    # Image Search URLs
    path('search/manual-image/', manual_image_search, name='manual-image-search'),
    path('search/image-based/', image_based_search, name='image_based_search'),
    
    # Image Features Management URLs
    path('image-features/<str:item_type>/<uuid:item_id>/', 
         get_image_features, name='get-image-features'),
    path('image-features/<str:item_type>/<uuid:item_id>/regenerate/', 
         regenerate_image_features, name='regenerate-image-features'),
    
    # Admin Verification URLs
    path('admin/verify/lost-item/<uuid:item_id>/', verify_lost_item, name='verify-lost-item'),
    path('admin/verify/found-item/<uuid:item_id>/', verify_found_item, name='verify-found-item'),
    
    # NEW SEARCH ENDPOINTS
    # Lost Items Search
    path('lost-items/search/', 
         LostItemViewSet.as_view({'get': 'search'}), 
         name='lost-items-search'),
    
    # Found Items Search  
    path('found-items/search/', 
         FoundItemViewSet.as_view({'get': 'search'}), 
         name='found-items-search'),
    
    # My Items endpoints
    path('lost-items/my-lost-items/', 
         LostItemViewSet.as_view({'get': 'my_lost_items'}), 
         name='my-lost-items'),
    
    path('found-items/my-found-items/', 
         FoundItemViewSet.as_view({'get': 'my_found_items'}), 
         name='my-found-items'),
    
    # Item Status Management
    path('found-items/<uuid:pk>/mark-returned/', 
         FoundItemViewSet.as_view({'post': 'mark_returned'}), 
         name='mark-item-returned'),
    
    # Claim Management
    path('claims/<uuid:pk>/approve/', 
         ClaimViewSet.as_view({'post': 'approve_claim'}), 
         name='approve-claim'),
    
    path('claims/<uuid:pk>/reject/', 
         ClaimViewSet.as_view({'post': 'reject_claim'}), 
         name='reject-claim'),
    
    # Notification Management
    path('notifications/unread-count/', 
         NotificationViewSet.as_view({'get': 'unread_count'}), 
         name='unread-notifications-count'),
    
    path('notifications/<uuid:pk>/mark-read/', 
         NotificationViewSet.as_view({'post': 'mark_read'}), 
         name='mark-notification-read'),
    
    path('notifications/mark-all-read/', 
         NotificationViewSet.as_view({'post': 'mark_all_read'}), 
         name='mark-all-notifications-read'),
]
